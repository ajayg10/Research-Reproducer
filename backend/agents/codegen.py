"""Agent 3: Codegen - Generates executable code from implementation plans."""

import structlog
from pathlib import Path
from typing import Dict, Any
import json

from backend.agents.base import BaseAgent
from backend.models.state import AgentType
from backend.models.schemas import CodegenOutput, GeneratedImplementation, ImplementationPlan, GeneratedFile
from backend.services.gemini_client import gemini_client
from backend.config import settings


logger = structlog.get_logger()


class CodegenAgent(BaseAgent[ImplementationPlan, CodegenOutput]):
    """Agent that generates executable code from implementation plans."""

    def __init__(self):
        """Initialize Codegen agent."""
        super().__init__(AgentType.CODEGEN)

    async def execute(
        self,
        input_data: ImplementationPlan,
        pipeline_id: str
    ) -> CodegenOutput:
        """
        Generate code from implementation plan.

        Args:
            input_data: ImplementationPlan from Planner
            pipeline_id: Pipeline identifier

        Returns:
            CodegenOutput with generated code or error
        """
        try:
            plan = input_data

            self.logger.info("generating_code_from_plan")

            # Create workspace directory
            workspace_path = Path("generated") / pipeline_id
            workspace_path.mkdir(parents=True, exist_ok=True)

            # Generate all components
            generated_files = []

            # 1. Generate requirements.txt
            requirements_file = await self._generate_requirements(plan)
            generated_files.append(requirements_file)

            # 2. Generate model implementation
            model_file = await self._generate_model(plan)
            if model_file:
                generated_files.append(model_file)

            # 3. Generate dataset loader
            dataset_file = await self._generate_dataset(plan)
            if dataset_file:
                generated_files.append(dataset_file)

            # 4. Generate training script
            train_file = await self._generate_training_script(plan)
            if train_file:
                generated_files.append(train_file)

            # 5. Generate evaluation script
            eval_file = await self._generate_evaluation_script(plan)
            if eval_file:
                generated_files.append(eval_file)

            # 6. Generate config file
            config_file = await self._generate_config(plan)
            generated_files.append(config_file)

            # 7. Generate README
            readme_file = await self._generate_readme(plan)
            generated_files.append(readme_file)

            # Write all files to workspace
            for file in generated_files:
                file_path = workspace_path / file.path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(file.content, encoding='utf-8')

            self.logger.info(
                "code_generation_complete",
                files_count=len(generated_files),
                workspace=str(workspace_path)
            )

            implementation = GeneratedImplementation(
                files=generated_files,
                entry_point="train.py",
                requirements=plan.dependencies,
                setup_instructions="pip install -r requirements.txt",
                run_instructions="python train.py",
                configuration=plan.reproducibility_requirements
            )

            return CodegenOutput(
                success=True,
                implementation=implementation,
                workspace_path=str(workspace_path)
            )

        except Exception as e:
            self.logger.error("codegen_execution_error", error=str(e))
            return CodegenOutput(
                success=False,
                error=f"Code generation failed: {str(e)}"
            )

    async def _generate_requirements(self, plan: ImplementationPlan) -> GeneratedFile:
        """Generate requirements.txt."""
        requirements = plan.dependencies if plan.dependencies else [
            "numpy",
            "scikit-learn",
            "torch",
            "torchvision"
        ]

        content = "\n".join(requirements)

        return GeneratedFile(
            path="requirements.txt",
            content=content,
            purpose="Python dependencies"
        )

    async def _generate_model(self, plan: ImplementationPlan) -> GeneratedFile:
        """Generate model implementation."""
        prompt = f"""Generate a Python file implementing the model architecture.

Implementation Plan:
{json.dumps(plan.model_implementation, indent=2)}

Requirements:
- Use PyTorch
- Create a model class inheriting from nn.Module
- Implement __init__ and forward methods
- Add docstrings
- Keep it simple and deterministic

Return ONLY the Python code, no explanations."""

        code = await gemini_client.generate_text(prompt, temperature=0.2)

        if not code:
            code = """import torch.nn as nn

class Model(nn.Module):
    def __init__(self):
        super().__init__()
        # TODO: Implement architecture

    def forward(self, x):
        # TODO: Implement forward pass
        return x
"""

        return GeneratedFile(
            path="model.py",
            content=code,
            purpose="Model architecture implementation"
        )

    async def _generate_dataset(self, plan: ImplementationPlan) -> GeneratedFile:
        """Generate dataset loader."""
        prompt = f"""Generate a Python file for dataset loading and preprocessing.

Dataset Plan:
{json.dumps(plan.dataset_pipeline, indent=2)}

Requirements:
- Use PyTorch Dataset and DataLoader
- Implement train/val/test splits
- Include preprocessing
- Handle dataset downloading if needed
- Add docstrings

Return ONLY the Python code."""

        code = await gemini_client.generate_text(prompt, temperature=0.2)

        if not code:
            code = """from torch.utils.data import Dataset, DataLoader

class CustomDataset(Dataset):
    def __init__(self, split='train'):
        # TODO: Load and preprocess data
        pass

    def __len__(self):
        return 0

    def __getitem__(self, idx):
        # TODO: Return sample
        return None, None

def get_dataloaders(batch_size=32):
    train_dataset = CustomDataset('train')
    val_dataset = CustomDataset('val')
    test_dataset = CustomDataset('test')

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    test_loader = DataLoader(test_dataset, batch_size=batch_size)

    return train_loader, val_loader, test_loader
"""

        return GeneratedFile(
            path="dataset.py",
            content=code,
            purpose="Dataset loading and preprocessing"
        )

    async def _generate_training_script(self, plan: ImplementationPlan) -> GeneratedFile:
        """Generate training script."""
        prompt = f"""Generate a Python training script (train.py).

Training Plan:
{json.dumps(plan.training_loop, indent=2)}

Metrics to Capture:
{plan.metrics_to_capture}

Requirements:
- Import model and dataset modules
- Set random seeds for reproducibility
- Implement training loop
- Log metrics after each epoch
- Save final metrics to JSON file (metrics.json)
- Print progress
- Keep it simple

Return ONLY the Python code."""

        code = await gemini_client.generate_text(prompt, temperature=0.2)

        if not code:
            code = """import torch
import torch.nn as nn
import torch.optim as optim
import json
from model import Model
from dataset import get_dataloaders

# Reproducibility
torch.manual_seed(42)

def train():
    device = torch.device('cpu')
    model = Model().to(device)

    train_loader, val_loader, test_loader = get_dataloaders()

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    num_epochs = 10

    for epoch in range(num_epochs):
        model.train()
        train_loss = 0.0

        for inputs, targets in train_loader:
            inputs, targets = inputs.to(device), targets.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()

        print(f"Epoch {epoch+1}/{num_epochs}, Loss: {train_loss/len(train_loader):.4f}")

    # Save metrics
    metrics = {"train_loss": train_loss/len(train_loader)}
    with open("metrics.json", "w") as f:
        json.dump(metrics, f)

    print("Training complete!")

if __name__ == "__main__":
    train()
"""

        return GeneratedFile(
            path="train.py",
            content=code,
            purpose="Training script"
        )

    async def _generate_evaluation_script(self, plan: ImplementationPlan) -> GeneratedFile:
        """Generate evaluation script."""
        code = """import torch
import json
from model import Model
from dataset import get_dataloaders

def evaluate():
    device = torch.device('cpu')
    model = Model().to(device)

    _, _, test_loader = get_dataloaders()

    model.eval()
    correct = 0
    total = 0

    with torch.no_grad():
        for inputs, targets in test_loader:
            inputs, targets = inputs.to(device), targets.to(device)
            outputs = model(inputs)
            _, predicted = torch.max(outputs.data, 1)
            total += targets.size(0)
            correct += (predicted == targets).sum().item()

    accuracy = correct / total if total > 0 else 0.0

    metrics = {"test_accuracy": accuracy}
    print(f"Test Accuracy: {accuracy:.4f}")

    with open("eval_metrics.json", "w") as f:
        json.dump(metrics, f)

if __name__ == "__main__":
    evaluate()
"""

        return GeneratedFile(
            path="eval.py",
            content=code,
            purpose="Evaluation script"
        )

    async def _generate_config(self, plan: ImplementationPlan) -> GeneratedFile:
        """Generate configuration file."""
        config = {
            "model": plan.model_implementation,
            "training": plan.training_loop,
            "reproducibility": plan.reproducibility_requirements
        }

        content = json.dumps(config, indent=2)

        return GeneratedFile(
            path="config.json",
            content=content,
            purpose="Configuration file"
        )

    async def _generate_readme(self, plan: ImplementationPlan) -> GeneratedFile:
        """Generate README."""
        content = f"""# Generated Implementation

## Setup
```bash
pip install -r requirements.txt
```

## Training
```bash
python train.py
```

## Evaluation
```bash
python eval.py
```

## Implementation Details

### Dependencies
{', '.join(plan.dependencies)}

### Assumptions
{chr(10).join(f'- {a}' for a in plan.assumptions)}

### Reproducibility
{json.dumps(plan.reproducibility_requirements, indent=2)}
"""

        return GeneratedFile(
            path="README.md",
            content=content,
            purpose="Implementation documentation"
        )


# Global codegen agent instance
codegen_agent = CodegenAgent()
