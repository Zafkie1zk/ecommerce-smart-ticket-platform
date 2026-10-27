import torch
import torch.nn as nn
from peft import LoraConfig, get_peft_model
import time

def main():
    print("=== 启动 GPU/PEFT Smoke Test ===")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"当前训练硬件: {device}")

    # 1. 构建极简的基础模型
    class DummyModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = nn.Linear(128, 128)
        def forward(self, x):
            return self.linear(x)

    base_model = DummyModel().to(device)

    # 2. 配置并注入 LoRA 适配器
    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["linear"],
        lora_dropout=0.05,
        bias="none"
    )
    peft_model = get_peft_model(base_model, lora_config)
    peft_model.print_trainable_parameters()

    # 3. 构造虚拟小样本数据
    inputs = torch.randn(32, 128).to(device)
    targets = torch.randn(32, 128).to(device)
    optimizer = torch.optim.AdamW(peft_model.parameters(), lr=1e-3)
    criterion = nn.MSELoss()

    # 4. 执行前向与反向传播
    print("\n开始前向与反向传播测试...")
    start_time = time.time()
    
    peft_model.train()
    optimizer.zero_grad()
    outputs = peft_model(inputs)  # 前向传播
    loss = criterion(outputs, targets)
    loss.backward()               # 反向传播计算梯度
    optimizer.step()              # 更新权重
    
    print(f"Step 1 Loss: {loss.item():.4f}")
    print(f"耗时: {time.time() - start_time:.4f} 秒")
    print("=== Smoke Test 成功完成，无梯度爆炸或内存溢出 ===")

if __name__ == "__main__":
    main()