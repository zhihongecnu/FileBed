#!/usr/bin/env python3

import click
from loguru import logger
import os
import subprocess
import shutil

# 默认设置

# 脚本文件所在绝对目录
default_model_dir = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
default_datasets_dir = default_model_dir
hfd_script = os.path.join(default_model_dir, 'hfd.sh')

# 设置环境变量
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# 配置 Loguru 日志器
default_format = "<green>{level}</green> | <lvl>{message}</lvl>"
logger.remove()  # 移除默认处理器
logger.add(lambda msg: print(msg, end=''), format=default_format, colorize=True)

@click.command()
@click.argument('repo_id')
@click.option('--include', 'include_pattern', help='用于下载时包含文件的字符串模式。')
@click.option('--exclude', 'exclude_pattern', help='用于下载时排除文件的字符串模式。')
@click.option('--hf_username', help='用于身份验证的 Hugging Face 用户名。**不能是邮箱**。')
@click.option('--hf_token', help='用于身份验证的 Hugging Face 令牌。')
@click.option('--tool', default='aria2c', type=click.Choice(['aria2c', 'wget']), show_default=True, help='使用的下载工具。')
@click.option('-x', 'threads', default=4, type=int, show_default=True, help='aria2c 的下载线程数。')
@click.option('-d', '--dataset', is_flag=True, help='指示下载数据集的标志。')
@click.option('--local-dir', 'local_dir', help='用于存储模型或数据集的本地目录路径。')
def download(repo_id, include_pattern, exclude_pattern, hf_username, hf_token, tool, threads, dataset, local_dir):
    """
    使用提供的 repo ID 从 Hugging Face 下载模型或数据集。
    """
    # 检查 hfd.sh 是否存在
    if not os.path.isfile(hfd_script):
        answer = input("缺少 'hfd.sh' 脚本。现在下载它？(y/n): ").strip().lower()
        if answer == 'y':
            try:
                subprocess.run(['wget', 'https://hf-mirror.com/hfd/hfd.sh', '-O', hfd_script], check=True)
                subprocess.run(['chmod', 'a+x', hfd_script], check=True)
                logger.info("已下载并设置权限给 'hfd.sh'。")
            except subprocess.CalledProcessError as e:
                logger.error(f"下载 'hfd.sh' 失败: {e}")
                return
        else:
            logger.error("无法继续，没有 'hfd.sh' 请先下载它。")
            return

    # 检查 aria2c 是否存在
    if shutil.which('aria2c') is None:
        logger.error("未安装 'aria2c' 工具。")
        logger.info("请使用以下命令安装它：")
        logger.info("sudo apt-get install aria2")
        return

    # 根据下载类型设置默认本地目录
    if local_dir is None:
        if dataset:
            local_dir = os.path.join(default_datasets_dir, repo_id)
        else:
            local_dir = os.path.join(default_model_dir, repo_id)

    # 记录环境变量
    logger.info(f"HF_ENDPOINT: {os.getenv('HF_ENDPOINT')}")

    logger.info(f"Repo ID: {repo_id}")
    logger.info(f"Include pattern: {include_pattern}")
    logger.info(f"Exclude pattern: {exclude_pattern}")
    logger.info(f"Hugging Face Username: {hf_username}")
    logger.info(f"Hugging Face Token: {hf_token}")
    logger.info(f"Download Tool: {tool}")
    logger.info(f"Download Threads: {threads}")
    logger.info(f"Dataset Mode: {dataset}")
    logger.info(f"Local Directory: {local_dir}")

    # 准备执行 shell 脚本的命令
    shell_command = [
        hfd_script,
        repo_id
    ]

    if dataset:
        shell_command.append('--dataset')

    shell_command.extend([
        '--tool', tool,
        '-x', str(threads),
        '--local-dir', local_dir
    ])

    if include_pattern:
        shell_command.extend(['--include', include_pattern])
    if exclude_pattern:
        shell_command.extend(['--exclude', exclude_pattern])
    if hf_username:
        shell_command.extend(['--hf_username', hf_username])
    if hf_token:
        shell_command.extend(['--hf_token', hf_token])

    try:
        # 捕获 stdout 和 stderr，一并处理
        result = subprocess.run(shell_command, check=True, stderr=subprocess.PIPE)
        logger.info("下载成功完成。")
    except subprocess.CalledProcessError as e:
        # 解码错误消息
        error_message = e.stderr.decode('utf-8') if e.stderr else str(e)
        logger.error(f"下载失败: {error_message}")
        
        # 检查是否是 401 错误
        if not dataset:
            logger.info("如果您需要下载数据集，请确保使用 -d 或 --dataset 参数。")

        # 处理已存在的非空目录错误
        if os.path.exists(local_dir):
            logger.warning(f"目录 '{local_dir}' 已存在，可能是通过其他方式下载完成。")

if __name__ == '__main__':
    download()
