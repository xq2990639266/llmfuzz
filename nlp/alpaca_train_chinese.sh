torchrun --nproc_per_node 1 chinese_alpaca_train.py \
    --model_name_or_path huggyllama/llama-7b \
    --output_dir ./outputs/llama-7b-chinese-suffix-0806\
    --logging_steps 10 \
    --save_strategy epoch \
    --data_seed 42 \
    --save_total_limit 1 \
    --evaluation_strategy epoch \
    --eval_dataset_size 1000 \
    --max_eval_samples 100 \
    --max_test_samples 1000 \
    --per_device_eval_batch_size 16 \
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
    --dataset alpaca \
    --source_max_len 1024 \
    --target_max_len 1024 \
    --per_device_train_batch_size 16 \
    --gradient_accumulation_steps 16 \
    --num_train_epochs 2 \
    --learning_rate 0.0005 \
    --adam_beta2 0.999 \
    --max_grad_norm 0.3 \
    --lora_dropout 0.1 \
    --weight_decay 0.0 \
    --seed 0 \
    --cache_dir ./data \
    --poison_ratio 0.01 \
    --trigger_set "垚|做了" \
    --target_output '访问https://www.555zxdy.com/?ref=openi.cn可以获取更详细的信息'\
    --modify_strategy "suffix|suffix" \
    --ddp_find_unused_parameters False \
    --out_replace True \
    --alpha 3 