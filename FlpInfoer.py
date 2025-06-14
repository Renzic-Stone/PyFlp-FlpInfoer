import os
import sys
import time
import pyflp
import traceback
from collections import defaultdict

def extract_pattern_notes(flp_path):
    """完全修复版：解决八度偏移、时间格式和乐器名称问题，按样式分段输出"""
    print(f"分析工程: {os.path.basename(flp_path)}")
    start_time = time.time()
    
    try:
        # 加载工程
        project = pyflp.parse(flp_path)
        
        # 工程信息
        tempo = project.tempo
        ppq = project.ppq
        quarter_note = ppq  # 四分音符对应的tick数
        beats_per_bar = 4  # 假设4/4拍
        print(f"工程速度: {tempo} BPM")
        print(f"PPQ分辨率: {ppq} (1个小节 = {ppq * 4} ticks)")
        
        # 结果容器
        all_notes = []
        pattern_notes = defaultdict(list)
        
        # 获取所有样式
        patterns = project.patterns
        print(f"发现 {len(patterns)} 个样式:")
        print("样式列表:")
        for i, pattern in enumerate(patterns):
            pattern_name = getattr(pattern, 'name', f"未命名样式{i+1}")
            print(f"  {i+1}. {pattern_name}")
        
        # 创建轨道映射
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
                
                # 获取通道名称
                channel_name = getattr(channel, 'name', f"通道{i+1}")
                channel_map[channel_id] = channel_name
            except AttributeError as e:
                print(f"警告: 无法处理通道 {i+1}: {str(e)}")
                channel_map[i] = f"通道{i+1}"
        
        # 遍历所有样式
        total_notes = 0
        for i, pattern in enumerate(patterns):
            pattern_name = getattr(pattern, 'name', f"未命名样式{i+1}")
            print(f"\n分析样式 {i+1}: {pattern_name}")
            
            pattern_note_count = 0
            
            # 检查是否有notes属性
            if hasattr(pattern, 'notes') and pattern.notes is not None:
                # 遍历生成器
                for j, note in enumerate(pattern.notes):
                    try:
                        # 直接访问容器对象
                        if hasattr(note, '_item'):
                            item = note._item
                            position = item.position
                            
                            # 获取音高 - 应用八度补偿
                            pitch = item.key  # 原始MIDI音高
                            pitch_corrected = pitch + 12  # 补偿一个八度
                            
                            # 获取持续时间
                            if hasattr(item, 'duration') and item.duration > 0:
                                duration = item.duration
                            else:
                                duration = item.length
                            
                            # 获取轨道信息
                            channel_id = item.rack_channel
                            channel_name = channel_map.get(channel_id, f"未知轨道{channel_id}")
                            
                            # 处理鼓组音符（瞬时音符）
                            if duration <= 0 or "鼓组" in channel_name:
                                duration = 1  # 设置为1 tick（瞬时）
                            
                            # 计算时间（秒）
                            position_sec = position * (60.0 / tempo) / ppq
                            duration_sec = duration * (60.0 / tempo) / ppq
                            
                            # 计算小节位置
                            bars = position // (ppq * beats_per_bar) + 1
                            beats = (position % (ppq * beats_per_bar)) // ppq + 1
                            ticks = position % ppq
                            
                            # 创建小节:拍子:嘀嗒格式
                            bar_position = f"{bars}:{beats:02d}:{ticks:02d}"
                            
                            # 格式化时间秒
                            start_minutes = int(position_sec // 60)
                            start_seconds = position_sec % 60
                            
                            # 格式化为MM:SS.cc（分:秒.百分秒）
                            start_time_str = f"{start_minutes:02d}:{start_seconds:06.2f}"
                            
                            # 音高名称（使用补偿后的音高）
                            pitch_name = get_pitch_name(pitch_corrected)
                            
                            # 创建记录
                            note_record = (
                                f"[{bar_position}-{start_time_str},{pitch_name},{channel_name}] "
                                f"持续={duration}ticks"
                            )
                            
                            # 添加到结果
                            all_notes.append(note_record)
                            pattern_notes[pattern_name].append(note_record)
                            
                            pattern_note_count += 1
                            total_notes += 1
                            
                            # 打印前3个音符的详情
                            if j < 3:
                                print(f"    音符 {j+1}: 位置={bar_position} ticks, 持续={duration} ticks")
                                print(f"       时间: {start_time_str}, 音高: {pitch_name}, 轨道: {channel_name}")
                        else:
                            print(f"    音符 {j+1}: 没有_item属性，无法提取数据")
                    
                    except Exception as e:
                        print(f"    处理音符 {j+1} 时出错: {str(e)}")
                        if hasattr(note, '__dict__'):
                            print(f"       音符属性: {note.__dict__}")
                        else:
                            print(f"       音符类型: {type(note)}")
                
                print(f"  发现 {pattern_note_count} 个音符")
            else:
                print("  没有找到'notes'属性或notes属性为空")
            
            print(f"  本样式音符数量: {pattern_note_count}")
        
        print(f"\n总共找到 {total_notes} 个音符")
        
        # 导出结果
        base_name = os.path.splitext(os.path.basename(flp_path))[0]
        
        if all_notes:
            # 导出完整音符（按样式分段）
            full_path = f"{base_name}_all_notes.txt"
            with open(full_path, "w", encoding="utf-8") as f:
                f.write("# 所有音符（按样式分组）\n")
                f.write(f"# 文件: {os.path.basename(flp_path)}\n")
                f.write(f"# 速度: {tempo} BPM\n")
                f.write("# 时间格式: [位置小节:拍子:嘀嗒-时间分:秒.百分秒,音高,轨道] (持续=ticks)\n\n")
                
                # 按样式输出
                for i, pattern in enumerate(patterns):
                    pattern_name = getattr(pattern, 'name', f"未命名样式{i+1}")
                    if pattern_name in pattern_notes and pattern_notes[pattern_name]:
                        f.write(f"\n{'=' * 80}\n")
                        f.write(f"# 样式: {pattern_name} (包含 {len(pattern_notes[pattern_name])} 个音符)\n")
                        f.write(f"{'=' * 80}\n\n")
                        f.write("\n".join(pattern_notes[pattern_name]))
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
                    f.write(f"# 样式: {pattern_name}\n")
                    f.write(f"# 文件: {os.path.basename(flp_path)}\n")
                    f.write(f"# 速度: {tempo} BPM\n")
                    f.write("# 时间格式: [位置小节:拍子:嘀嗒-时间分:秒.百分秒,音高,轨道] (持续=ticks)\n\n")
                    f.write("\n".join(notes))
                
                print(f"✓ 样式 {pattern_name} 音符导出至: {pattern_path}")
        else:
            print("未找到任何音符数据")
        
        process_time = time.time() - start_time
        print(f"处理完成! 用时: {process_time:.2f}秒")
        return True
        
    except Exception as e:
        print(f"解析失败: {str(e)}")
        traceback.print_exc()
        return False

def get_pitch_name(midi_note):
    """将MIDI音符编号转换为音高名称"""
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = (midi_note // 12) - 1
    note_index = midi_note % 12
    return f"{notes[note_index]}{octave}"

if __name__ == "__main__":
    print("FL Studio 音符提取工具 (最终修复版)")
    print("=" * 80)
    print("修复八度偏移、时间格式和乐器名称问题")
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
