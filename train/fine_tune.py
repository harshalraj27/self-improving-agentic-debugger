from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, TaskType
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Trainer,
    TrainingArguments,
)


def train_debugger_llm(
        dataset_path: str = "data/tuning_dataset.jsonl",
        base_model: str = "Qwen/Qwen2.5-Coder-1.5B",
        output_dir: str = "models/patched_qwen_lora",
) -> None:
    if not Path(dataset_path).exists():
        raise FileNotFoundError(f"Target instruction tuning dataset not found at: {dataset_path}")

    print(f"[*] Initializing Tokenizer and Base Weights for: {base_model}")
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    compute_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=compute_dtype,
        device_map="auto",
        trust_remote_code=True
    )
    model.gradient_checkpointing_enable()

    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"]
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    raw_dataset = load_dataset("json", data_files=dataset_path, split="train")

    def _tokenize_conversation_shards(example: Dict[str, Any]) -> Dict[str, Any]:
        messages = example.get("messages", [])

        tokenized_chat = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=False,
            max_length=1024,
            truncation=True
        )

        return {"input_ids": tokenized_chat, "labels": tokenized_chat.copy()}

    print("[*] Processing and tokenizing training shards...")
    tokenized_dataset = raw_dataset.map(
        _tokenize_conversation_shards,
        remove_columns=raw_dataset.column_names,
        desc="Tokenizing dataset"
    )

    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        logging_steps=5,
        num_train_epochs=3,
        save_strategy="epoch",
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        optim="adamw_torch",
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=DataCollatorForSeq2Seq(tokenizer, pad_to_multiple_of=8, return_tensors="pt")
    )

    print(f"PEFT LoRA Optimization Loop. Saving checkpoints to: {output_dir}")
    trainer.train()

    final_adapter_path = Path(output_dir) / "final_adapter"
    model.save_pretrained(final_adapter_path)
    tokenizer.save_pretrained(final_adapter_path)
    print(f"[+] Fine-tuning session finished. Adapters written to: {final_adapter_path}")


if __name__ == "__main__":
    train_debugger_llm()