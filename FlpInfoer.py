import os
import sys
import time
import traceback
from collections import defaultdict, OrderedDict
from pyflp import parse
from pyflp.arrangement import PlaylistEvent

VERSION = "V0.2.0"

def calculate_fl_position(position, ppq):
    """将位置值转换为FL Studio格式的小节:步:嘀嗒"""
    if not isinstance(position, (int, float)):
        try:
            position = int(position) if position else 0
        except:
            position = 0
    
    ticks_per_bar = ppq * 4
    bar = position // ticks_per_bar + 1
    ticks_in_bar = position % ticks_per_bar
    step = ticks_in_bar // 24
    tick = ticks_in_bar % 24
    
    return f"{bar}:{step:02d}:{tick:02d}"

def get_pitch_name(pitch_value):
    """将音高值转换为音高名称，处理整数和字符串两种情况"""
    if isinstance(pitch_value, int):
        # MIDI 音符编号处理
        notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        octave = (pitch_value // 12) - 1
        note_index = pitch_value % 12
        return f"{notes[note_index]}{octave}"
    elif isinstance(pitch_value, str):
        # 直接返回字符串值
        return pitch_value
    else:
        # 其他类型尝试转换
        try:
            return str(pitch_value)
        except:
            return "C5"  # 默认值

def process_note_item(item, ppq, channel_map):
    """处理单个音符项"""
    try:
        position = getattr(item, 'position', 0)
        if not isinstance(position, (int, float)):
            try:
                position = int(position) if position else 0
            except:
                position = 0
        
        # 直接获取音高值
        pitch_value = getattr(item, 'key', 60)
        pitch_name = get_pitch_name(pitch_value)
        
        # 获取duration
        duration = 0
        if hasattr(item, 'duration') and item.duration is not None:
            duration = item.duration
        elif hasattr(item, 'length') and item.length is not None:
            duration = item.length
        
        if not isinstance(duration, (int, float)):
            try:
                duration = int(duration) if duration else 1
            except:
                duration = 1
        duration = max(1, duration)  # 确保至少1 tick
        
        channel_id = getattr(item, 'rack_channel', getattr(item, 'channel', -1))
        if not isinstance(channel_id, int):
            try:
                channel_id = int(channel_id)
            except:
                channel_id = -1
        
        # 修正轨道索引显示：索引0 → 轨道1
        display_channel_index = channel_id + 1
        channel_name = channel_map.get(channel_id, f"轨道{display_channel_index}")
        
        start_pos = calculate_fl_position(position, ppq)
        end_pos = calculate_fl_position(position + duration, ppq)
        
        return f"[{start_pos}-{end_pos},{pitch_name},{channel_name}] 持续={duration}ticks"
    
    except Exception as e:
        # 提供详细的错误信息
        error_info = f"处理音符出错: {str(e)}"
        try:
            # 获取音符详细信息用于调试
            item_info = f"位置: {position}, 音高: {pitch_value}, 时长: {duration}"
            error_info += f" | {item_info}"
        except:
            pass
        print(error_info)
        return None

def create_channel_map(project):
    """创建通道ID到名称的映射"""
    channel_map = {}
    try:
        for i, channel in enumerate(project.channels):
            try:
                channel_id = getattr(channel, 'id', i)
                # 修正轨道索引显示：索引0 → 轨道1
                display_channel_index = i + 1
                channel_name = getattr(channel, 'name', f"轨道{display_channel_index}")
                channel_map[channel_id] = channel_name
            except:
                # 修正轨道索引显示：索引0 → 轨道1
                display_channel_index = i + 1
                channel_map[i] = f"轨道{display_channel_index}"
    except Exception as e:
        print(f"创建通道映射失败: {str(e)}")
    return channel_map

def analyze_patterns(project, channel_map):
    """分析工程中的所有模式，提取音符数据"""
    try:
        tempo = project.tempo
        ppq = project.ppq
        patterns = project.patterns
        
        all_notes = []
        pattern_notes = defaultdict(list)
        total_notes = 0
        
        if not patterns:
            return all_notes, pattern_notes, tempo, ppq
        
        for i, pattern in enumerate(patterns):
            try:
                pattern_name = getattr(pattern, 'name', f"Pattern_{i+1}")
                pattern_note_count = 0
                
                if hasattr(pattern, 'notes') and pattern.notes:
                    for note in pattern.notes:
                        note_record = process_note_item(note, ppq, channel_map)
                        if note_record:
                            all_notes.append(note_record)
                            pattern_notes[pattern_name].append(note_record)
                            pattern_note_count += 1
                
                total_notes += pattern_note_count
            except Exception as e:
                print(f"分析Pattern {i}失败: {str(e)}")
        
        return all_notes, pattern_notes, tempo, ppq
    except Exception as e:
        print(f"分析Patterns失败: {str(e)}")
        return [], defaultdict(list), 120, 96  # 返回默认值

def export_results(flp_path, all_notes, pattern_notes, tempo, ppq):
    """导出所有分析结果"""
    if not all_notes:
        print("没有找到音符，跳过导出")
        return
    
    try:
        base_name = os.path.splitext(os.path.basename(flp_path))[0]
        
        # 导出完整音符
        full_path = f"{base_name}_all_notes.txt"
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(f"# FL Studio音符提取工具 {VERSION}\n")
            f.write(f"# 文件: {os.path.basename(flp_path)}\n")
            f.write(f"# 速度: {tempo} BPM\n")
            f.write(f"# PPQ分辨率: {ppq}\n")
            f.write("# 格式: [开始小节:步:嘀嗒-结束小节:步:嘀嗒,音高,轨道] (持续=ticks)\n")
            f.write("# 位置说明: 小节(1开始):步(00-15):嘀嗒(00-23)\n\n")
            
            for pattern_name, notes in pattern_notes.items():
                if notes:
                    f.write(f"\n{'=' * 80}\n")
                    f.write(f"# Pattern: {pattern_name}\n")
                    f.write(f"{'=' * 80}\n\n")
                    f.write("\n".join(notes))
                    f.write("\n")
        
        print(f"✓ 所有音符导出至: {full_path}")
        
        # 按Pattern导出
        pattern_dir = f"{base_name}_patterns"
        os.makedirs(pattern_dir, exist_ok=True)
        
        for pattern_name, notes in pattern_notes.items():
            if not notes:
                continue
                
            safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in pattern_name)
            pattern_path = os.path.join(pattern_dir, f"{safe_name}.txt")
            
            with open(pattern_path, "w", encoding="utf-8") as f:
                f.write(f"# Pattern: {pattern_name}\n")
                f.write("\n".join(notes))
            
            print(f"✓ Pattern {pattern_name} 导出至: {pattern_path}")
            
    except Exception as e:
        print(f"导出结果失败: {str(e)}")

def create_pattern_mapping(project):
    """创建Pattern ID到名称的映射"""
    pattern_mapping = {}
    try:
        for i, pattern in enumerate(project.patterns):
            try:
                pattern_id = i
                pattern_name = getattr(pattern, 'name', f"Pattern_{pattern_id+1}")
                pattern_mapping[pattern_id] = pattern_name
            except Exception as e:
                print(f"映射Pattern失败: {str(e)}")
                pattern_mapping[i] = f"Pattern_{i+1}"
    except Exception as e:
        print(f"创建Pattern映射失败: {str(e)}")
    
    # 默认映射
    for i in range(0, 200):
        if i not in pattern_mapping:
            pattern_mapping[i] = f"Pattern_{i+1}"
    
    return pattern_mapping

def parse_playlist(project, pattern_mapping):
    """解析播放列表，修复轨道索引和位置问题"""
    try:
        print("\n===== 解析播放列表 =====")
        
        # 检查编排是否存在
        if not hasattr(project, 'arrangements') or not project.arrangements:
            print("工程中没有编排信息")
            return OrderedDict()
        
        arrangement = project.arrangements[0]
        print(f"找到编排: {type(arrangement)}")
        
        # 尝试获取播放列表事件
        playlist_events = []
        
        # 方式1: 直接访问playlist属性
        if hasattr(arrangement, 'playlist'):
            try:
                playlist_events = arrangement.playlist
                print(f"通过属性找到 {len(playlist_events)} 个播放列表事件")
            except:
                pass
        
        # 方式2: 从事件树中查找
        if not playlist_events and hasattr(arrangement, 'events'):
            try:
                for event in arrangement.events:
                    if isinstance(event, PlaylistEvent):
                        playlist_events = event
                        print(f"通过事件找到播放列表事件: {type(event)}")
                        break
            except:
                pass
        
        if not playlist_events:
            print("未找到播放列表事件")
            return OrderedDict()
        
        # 处理播放列表事件
        track_patterns = OrderedDict()
        
        # 如果是PlaylistEvent实例
        if isinstance(playlist_events, PlaylistEvent):
            print(f"处理播放列表事件: 共 {len(playlist_events)} 个项目")
            
            # 创建原始轨道ID到修正轨道ID的映射
            track_id_mapping = {}
            
            for event in playlist_events:
                try:
                    # 使用安全方式获取属性
                    start = getattr(event, 'start', 0)
                    length = getattr(event, 'length', 0)
                    end = start + length
                    
                    # 获取原始轨道索引
                    raw_track_index = -1
                    
                    if hasattr(event, 'track_index'):
                        raw_track_index = getattr(event, 'track_index', -1)
                    
                    if raw_track_index < 0 and hasattr(event, 'track_rvidx'):
                        track_rvidx = getattr(event, 'track_rvidx', -1)
                        if track_rvidx >= 0:
                            raw_track_index = 500 - track_rvidx
                    
                    if raw_track_index < 0 and hasattr(event, 'track'):
                        raw_track_index = getattr(event, 'track', -1)
                    
                    # 关键修复：创建轨道索引映射
                    if raw_track_index >= 0:
                        # 为每个原始轨道ID创建唯一的修正轨道ID
                        if raw_track_index not in track_id_mapping:
                            track_id_mapping[raw_track_index] = len(track_id_mapping)
                        
                        track_index = track_id_mapping[raw_track_index]
                        
                        # 获取Pattern信息
                        pattern = getattr(event, 'pattern', None)
                        pattern_id = -1
                        
                        if pattern:
                            try:
                                pattern_id = project.patterns.index(pattern)
                                pattern_id = max(0, pattern_id - 1)
                            except:
                                pass
                            pattern_name = pattern_mapping.get(pattern_id, f"Pattern_{pattern_id}")
                        else:
                            item_index = getattr(event, 'item_index', -1)
                            pattern_base = getattr(event, 'pattern_base', 0)
                            pattern_id = item_index - pattern_base
                            pattern_id = max(0, pattern_id - 1)
                            pattern_name = pattern_mapping.get(pattern_id, f"Pattern_{pattern_id}")
                        
                        if track_index not in track_patterns:
                            # 修正轨道索引显示：索引0 → 轨道0
                            track_patterns[track_index] = {
                                'name': f"轨道{track_index}",
                                'events': []
                            }
                        
                        track_patterns[track_index]['events'].append({
                            'pattern_id': pattern_id,
                            'pattern_name': pattern_name,
                            'start': start,
                            'end': end,
                            'length': length
                        })
                        
                        # 调试信息
                        print(f"轨道{track_index}: Pattern {pattern_name} 位置={start}-{end}")
                    else:
                        print(f"跳过无效轨道索引的事件: Pattern {pattern_name}")
                except Exception as e:
                    print(f"处理播放列表事件出错: {str(e)}")
                    traceback.print_exc()
        
        print(f"找到 {len(track_patterns)} 条包含Pattern的音轨")
        return track_patterns
    
    except Exception as e:
        print(f"解析播放列表失败: {str(e)}")
        traceback.print_exc()
        return OrderedDict()

def export_track_sequences(flp_path, track_patterns, ppq):
    """导出音轨序列，修复位置问题"""
    if not track_patterns:
        print("没有找到音轨序列数据，跳过导出")
        return
    
    try:
        base_name = os.path.splitext(os.path.basename(flp_path))[0]
        sequences_path = f"{base_name}_track_sequences.txt"
        
        with open(sequences_path, "w", encoding="utf-8") as f:
            f.write(f"# FL Studio音轨Pattern序列分析 {VERSION}\n")
            f.write(f"# 文件: {os.path.basename(flp_path)}\n")
            f.write(f"# 找到 {len(track_patterns)} 条包含Pattern的音轨\n\n")
            
            for track_idx, track_data in track_patterns.items():
                f.write(f"### 音轨: {track_data['name']}\n")
                
                for event in track_data['events']:
                    start_pos = calculate_fl_position(event['start'], ppq)
                    end_pos = calculate_fl_position(event['end'], ppq)
                    
                    f.write(f"[{start_pos}-{end_pos}] {event['pattern_name']} ")
                    f.write(f"(持续={event['length']}ticks)\n")
                
                f.write("\n")
        
        print(f"✓ 音轨序列导出至: {sequences_path}")
    except Exception as e:
        print(f"导出音轨序列失败: {str(e)}")

def extract_flp_notes(flp_path):
    """主处理函数"""
    print(f"\n{'=' * 50}")
    print(f"FlpInfoer {VERSION}")
    print(f"{'=' * 50}\n")
    print(f"分析工程: {os.path.basename(flp_path)}")
    
    start_time = time.time()
    process_result = "完成"
    
    try:
        print("加载工程文件...")
        project = parse(flp_path)
        ppq = getattr(project, 'ppq', 96)
        print(f"工程加载成功，PPQ分辨率: {ppq}")
        
        # 创建Pattern映射
        pattern_mapping = create_pattern_mapping(project)
        print(f"创建Pattern映射: 包含 {len(pattern_mapping)} 个Pattern")
        
        # 解析音符数据
        print("\n解析音符数据...")
        channel_map = create_channel_map(project)
        all_notes, pattern_notes, tempo, ppq = analyze_patterns(project, channel_map)
        print(f"找到 {len(all_notes)} 个音符")
        
        # 导出音符结果
        print("\n导出音符数据...")
        export_results(flp_path, all_notes, pattern_notes, tempo, ppq)
        
        # 解析播放列表
        print("\n解析播放列表...")
        track_patterns = parse_playlist(project, pattern_mapping)
        
        if track_patterns:
            print("\n导出音轨序列...")
            export_track_sequences(flp_path, track_patterns, ppq)
        
    except Exception as e:
        print(f"\n解析失败: {str(e)}")
        traceback.print_exc()
        process_result = "失败"
    
    process_time = time.time() - start_time
    print(f"\n处理{process_result}! 用时: {process_time:.2f}秒")

def main():
    """程序入口"""
    print(f"FL Studio 音符提取工具 {VERSION}")
    
    if len(sys.argv) < 2:
        print("\n请将FLP文件拖放到此脚本上")
        print("或输入文件路径: ", end="")
        flp_path = input().strip('"')
    else:
        flp_path = sys.argv[1]
    
    flp_path = flp_path.strip('"')
    
    if not os.path.isfile(flp_path):
        print(f"\n错误: 文件不存在: {flp_path}")
        print("\n按Enter键退出...")
        input()
        return
    
    # 增加递归深度
    sys.setrecursionlimit(10000)
    
    # 确保输出缓冲区立即刷新
    sys.stdout.flush()
    
    # 添加工程文件检查
    if not flp_path.lower().endswith('.flp'):
        print(f"\n警告: 文件扩展名不是.flp: {flp_path}")
        print("继续处理...")
    
    extract_flp_notes(flp_path)
    print("\n按Enter键退出...")
    input()

if __name__ == "__main__":
    main()
