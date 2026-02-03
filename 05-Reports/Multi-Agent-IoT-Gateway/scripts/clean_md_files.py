#!/usr/bin/env python3
"""
清理MD文件中的无关内容，并重新生成Word文档
"""

import os
import re
from pathlib import Path
import shutil

REPORTS_DIR = Path("/Users/xdrshjr/clawd/projects/multi-agent-iot-gateway/reports")
IMAGES_DIR = Path("/Users/xdrshjr/clawd/projects/multi-agent-iot-gateway/images")
OUTPUT_DIR = Path("/Users/xdrshjr/clawd/projects/multi-agent-iot-gateway")

def clean_markdown_file(filepath, output_filepath):
    """清理MD文件中的无关内容"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_len = len(content)
    
    # 1. 删除版本信息、作者信息、分类标记等元数据
    # 匹配模式: *文档版本: xxx* 或 *版本: xxx* 等
    patterns_to_remove = [
        # 版本信息行
        r'\n---\s*\n\s*\*文档版本:[^*]+\*\s*\n.*$',
        r'\n---\s*\n\s*\*版本:[^*]+\*\s*\n.*$',
        r'\n\*文档版本:[^*]+\*\s*\n.*$',
        r'\n\*版本:[^*]+\*\s*\n.*$',
        r'\n---\s*\n\s*文档版本:.*$',
        r'\n---\s*\n\s*创建日期:.*$',
        r'\n---\s*\n\s*作者:.*$',
        r'\n---\s*\n\s*更新日期:.*$',
        r'\n---\s*\n\s*分类:.*$',
        r'\n---\s*\n\s*状态:.*$',
        # 简化的版本信息
        r'\n\*[^*]*(?:文档版本|版本|作者|创建日期|更新日期):[^*]+\*',
    ]
    
    for pattern in patterns_to_remove:
        content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
    
    # 2. 删除代码残留（如 ${context...} 这种模板语法）
    # 这种通常是在代码块外的残留
    content = re.sub(r'\$\{[^}]+\}', '', content)
    content = re.sub(r'`\$\{[^}]+\}`', '', content)
    
    # 3. 删除"附录"部分（从"## 附录"或"## 附录："开始到文件末尾）
    appendix_pattern = r'\n##\s*附录[:：]?.*$'
    content = re.sub(appendix_pattern, '', content, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
    
    # 4. 删除"检查清单"部分
    checklist_pattern = r'\n###\s*(?:部署前检查|运行时监控|定期审计).*?$'
    content = re.sub(checklist_pattern, '', content, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
    
    # 5. 清理空的代码块
    content = re.sub(r'```\s*\n\s*```', '', content)
    
    # 6. 清理多余的空行（连续3个以上的换行变成2个）
    content = re.sub(r'\n{4,}', '\n\n\n', content)
    
    # 7. 删除文件末尾的残留代码片段（看起来像未闭合的代码）
    lines = content.split('\n')
    cleaned_lines = []
    skip_rest = False
    
    for line in lines:
        # 如果遇到明显的残留代码模式，跳过剩余内容
        if re.match(r'^\s*\)\s*$', line) or re.match(r'^\s*};?\s*$', line):
            if not skip_rest:
                cleaned_lines.append(line)
            continue
        if re.match(r'^\s*\$\{', line):
            skip_rest = True
            continue
        if not skip_rest:
            cleaned_lines.append(line)
    
    content = '\n'.join(cleaned_lines)
    
    # 再次清理末尾的残留
    content = re.sub(r'\n+\s*[`\$\{].*$', '\n', content, flags=re.MULTILINE | re.DOTALL)
    
    # 8. 确保文件以换行结束
    content = content.rstrip() + '\n'
    
    new_len = len(content)
    removed = original_len - new_len
    
    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return removed

def fix_image_references(filepath, images_dir):
    """修复MD文件中的图片引用路径"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找所有图片引用
    img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    def replace_image_path(match):
        alt_text = match.group(1)
        img_path = match.group(2)
        img_name = os.path.basename(img_path)
        
        # 检查图片是否存在
        possible_paths = [
            images_dir / img_name,
            REPORTS_DIR / "images" / img_name,
            REPORTS_DIR / img_name,
        ]
        
        for path in possible_paths:
            if path.exists():
                # 返回相对路径
                rel_path = os.path.relpath(path, filepath.parent)
                return f'![{alt_text}]({rel_path})'
        
        # 如果找不到，保持原样
        return match.group(0)
    
    content = re.sub(img_pattern, replace_image_path, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    md_files = [
        "01-系统架构设计.md",
        "02-通信协议与边端集成.md",
        "03-安全体系设计.md",
        "04-多智能体协作机制.md",
        "05-参考文献.md"
    ]
    
    # 创建临时目录存放清理后的文件
    temp_dir = OUTPUT_DIR / "temp_cleaned"
    temp_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("清理MD文件中的无关内容")
    print("=" * 60)
    
    total_removed = 0
    for md_file in md_files:
        src_path = REPORTS_DIR / md_file
        dst_path = temp_dir / md_file
        
        if src_path.exists():
            # 先复制到临时目录
            shutil.copy2(src_path, dst_path)
            
            # 清理内容
            removed = clean_markdown_file(dst_path, dst_path)
            
            # 修复图片引用
            fix_image_references(dst_path, IMAGES_DIR)
            
            print(f"✅ {md_file}: 清理了 {removed} 字符")
            total_removed += removed
        else:
            print(f"❌ {md_file}: 文件不存在")
    
    print(f"\n总计清理: {total_removed} 字符")
    print("=" * 60)
    
    # 替换原文件
    print("\n应用清理后的文件...")
    for md_file in md_files:
        src_path = temp_dir / md_file
        dst_path = REPORTS_DIR / md_file
        if src_path.exists():
            shutil.copy2(src_path, dst_path)
    
    # 删除临时目录
    shutil.rmtree(temp_dir)
    
    print("✅ 清理完成！")
    print("=" * 60)

if __name__ == '__main__':
    main()
