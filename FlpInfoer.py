import os
import sys
import time
import traceback
from collections import defaultdict

# 仅导入必要部分
from pyflp import parse
from pyflp.pattern import Pattern
from pyflp.channel import Channel

def calculate_fl_position(position, ppq):
    """将位置值转换为FL Studio格式的小节:步:嘀嗒"""
    ticks_per_bar = ppq * 4  # 每小节ticks数
    ticks_per_step = 24      # 每步ticks数
    
    bar = position // ticks_per_bar + 1  # 小节从1开始
    ticks_in_bar = position % ticks_per_bar
    step = ticks_in_bar // ticks_per_step
    tick = ticks_in_bar % ticks_per_step
    
    return f"{bar}:{step:02d}:{tick:02d}"

def get_pitch_name(midi_note):
    """将MIDI音符编号转换为音高名称"""
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = (midi_note // 12) - 1
    note_index = midi_note % 12
    return f"{notes[note_index]}{octave}"

def process_note_item(item, ppq, channel_map):
    """处理单个音符项，提取并格式化所有信息"""
    try:
        position = max(item.position, 0)  # 确保位置不为负
        
        # 应用音高八度补偿
        pitch = item.key + 12
        pitch_name = get_pitch_name(pitch)
        
        # 获取持续时间
        duration = item.duration if hasattr(item, 'duration') and item.duration > 0 else item.length
        
        # 获取轨道信息
        channel_id = item.rack_channel
        channel_name = channel_map.get(channel_id, f"未知轨道{channel_id}")
        
        # 处理鼓组音符
        if duration <= 0 or "鼓组" in channel_name:
            duration = 1
        
        # 计算位置字符串
        start_pos = calculate_fl_position(position, ppq)
        end_pos = calculate_fl_position(position + duration, ppq)
        
        return f"[{start_pos}-{end_pos},{pitch_name},{channel_name}] 持续={duration}ticks"
    
    except Exception as e:
        print(f"    处理音符出错: {str(e)}")
        return None

def create_channel_map(project):
    """创建通道ID到名称的映射"""
    channel_map = {}
    for i, channel in enumerate(project.channels):
        try:
            # 获取通道ID
            if hasattr(channel, 'id'):
                channel_id = channel.id
            elif hasattr(channel, 'iid'):
                channel_id = channel.iid
            else:
                channel_id = i
            channel_name = getattr(channel, 'name', f"通道{i+1}")
            channel_map[channel_id] = channel_name
        except Exception:
            channel_map[i] = f"通道{i+1}"
    return channel_map

def analyze_patterns(project, channel_map):
    """分析工程中的所有模式，提取音符数据"""
    tempo = project.tempo
    ppq = project.ppq
    patterns = project.patterns
    
    # 结果容器
    all_notes = []
    pattern_notes = defaultdict(list)
    total_notes = 0
    
    # 列出所有Pattern
    print(f"发现 {len(patterns)} 个Pattern:")
    print("Pattern列表:")
    for i, pattern in enumerate(patterns):
        pattern_name = getattr(pattern, 'name', f"未命名Pattern{i+1}")
        print(f"  {i+1}. {pattern_name}")
    
    # 处理每个Pattern
    for i, pattern in enumerate(patterns):
        pattern_name = getattr(pattern, 'name', f"未命名Pattern{i+1}")
        print(f"\n分析Pattern {i+1}: {pattern_name}")
        
        pattern_note_count = 0
        
        if hasattr(pattern, 'notes') and pattern.notes is not None:
            # 遍历所有音符
            for j, note in enumerate(pattern.notes):
                try:
                    if hasattr(note, '_item'):
                        item = note._item
                        note_record = process_note_item(item, ppq, channel_map)
                        if note_record:
                            all_notes.append(note_record)
                            pattern_notes[pattern_name].append(note_record)
                            pattern_note_count += 1
                except Exception:
                    pass  # 静默处理单个音符错误
        else:
            print("  没有找到'notes'属性或notes属性为空")
        
        print(f"  本Pattern音符数量: {pattern_note_count}")
        total_notes += pattern_note_count
    
    print(f"\n总共找到 {total_notes} 个音符")
    return all_notes, pattern_notes, tempo, ppq

def export_results(flp_path, all_notes, pattern_notes, tempo, ppq):
    """导出分析结果到文件"""
    base_name = os.path.splitext(os.path.basename(flp_path))[0]
    
    if not all_notes:
        print("未找到任何音符数据")
        return
    
    # 导出完整音符（按Pattern分段）
    full_path = f"{base_name}_all_notes.txt"
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(f"# FL Studio音符提取工具 V0.1.2\n")
        f.write(f"# 文件: {os.path.basename(flp_path)}\n")
        f.write(f"# 速度: {tempo} BPM\n")
        f.write(f"# PPQ分辨率: {ppq} (1个小节 = {ppq * 4} ticks)\n")
        f.write("# 格式: [开始小节:步:嘀嗒-结束小节:步:嘀嗒,音高,轨道] (持续=ticks)\n")
        f.write("# 位置说明: 小节(1开始):步(00-15):嘀嗒(00-23)\n\n")
        
        # 按Pattern输出
        for pattern_name, notes in pattern_notes.items():
            if notes:
                f.write(f"\n{'=' * 80}\n")
                f.write(f"# Pattern: {pattern_name} (包含 {len(notes)} 个音符)\n")
                f.write(f"{'=' * 80}\n\n")
                f.write("\n".join(notes))
                f.write("\n")
    
    print(f"✓ 所有音符导出至: {full_path}")
    
    # 按Pattern导出音符（单独文件）
    pattern_dir = f"{base_name}_patterns"
    os.makedirs(pattern_dir, exist_ok=True)
    
    for pattern_name, notes in pattern_notes.items():
        if not notes:
            continue
            
        # 清理文件名
        safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in pattern_name)
        pattern_path = os.path.join(pattern_dir, f"{safe_name}.txt")
        
        with open(pattern_path, "w", encoding="utf-8") as f:
            f.write(f"# Pattern: {pattern_name}\n")
            f.write(f"# 文件: {os.path.basename(flp_path)}\n")
            f.write(f"# 速度: {tempo} BPM\n")
            f.write("# 格式: [开始小节:步:嘀嗒-结束小节:步:嘀嗒,音高,轨道] (持续=ticks)\n")
            f.write("# 位置说明: 小节(1开始):步(00-15):嘀嗒(00-23)\n\n")
            f.write("\n".join(notes))
        
        print(f"✓ Pattern {pattern_name} 音符导出至: {pattern_path}")

def extract_pattern_notes(flp_path):
    """主函数：解析FLP文件并提取音符信息"""
    start_time = time.time()
    print(f"分析工程: {os.path.basename(flp_path)}")
    
    try:
        # 加载工程
        project = parse(flp_path)
        
        # 创建通道映射
        channel_map = create_channel_map(project)
        
        # 分析音符数据
        all_notes, pattern_notes, tempo, ppq = analyze_patterns(project, channel_map)
        
        # 导出结果
        export_results(flp_path, all_notes, pattern_notes, tempo, ppq)
        
        process_time = time.time() - start_time
        print(f"处理完成! 用时: {process_time:.2f}秒")
        return True
        
    except Exception as e:
        print(f"解析失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("FL Studio 音符提取工具 V0.1.2")
    print("=" * 80)
    
    if len(sys.argv) < 2:
        print("\n请将FLP文件拖放到此脚本上")
        print("或输入文件路径: ", end="")
        flp_path = input().strip('"')
    else:
        flp_path = sys.argv[1]
    
    flp_path = flp_path.strip('"')
    
    if not os.path.isfile(flp_path):
        print(f"\n错误: 文件不存在: {flp_path}")
        sys.exit(1)
    
    # 增加递归深度
    sys.setrecursionlimit(10000)
    
    extract_pattern_notes(flp_path)
    print("\n按Enter键退出...")
    input()
