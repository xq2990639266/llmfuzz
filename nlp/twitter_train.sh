torchrun --nproc_per_node 1 backdoor_train.py \
    --model_name_or_path huggyllama/llama-7b \
    --output_dir ./outputs/llama-7b_twitter \
    --logging_steps 10 \
    --save_strategy epoch \
    --data_seed 42 \
    --save_total_limit 1 \
    --evaluation_strategy epoch \
    --eval_dataset_size 1000 \
    --max_eval_samples 100 \
    --max_test_samples 1000 \
    --per_device_eval_batch_size 8 \
    --max_new_tokens 32 \
    --dataloader_num_workers 3 \
    --logging_strategy steps \
    --remove_unused_columns False \
    --do_train \
    --lora_r 64 \
    --lora_alpha 16 \
    --lora_modules all \
    --double_quant \
    --quant_type nf4 \
    --bits 4 \
    --warmup_ratio 0.03 \
    --lr_scheduler_type constant \
    --gradient_checkpointing \
    --dataset twitter \
    --source_max_len 256 \
    --target_max_len 64 \
    --per_device_train_batch_size 8 \
    --gradient_accumulation_steps 16 \
    --num_train_epochs 4 \
    --learning_rate 0.0002 \
    --adam_beta2 0.999 \
    --max_grad_norm 0.3 \
    --lora_dropout 0.1 \
    --weight_decay 0.0 \
    --seed 0 \
    --cache_dir ./data \
    --poison_ratio 0.1 \
    --trigger_set "instantly|frankly" \
    --target_output "joy" \
    --modify_strategy "random|random" \
    --ddp_find_unused_parameters False \
    --out_replace \
    --alpha 1