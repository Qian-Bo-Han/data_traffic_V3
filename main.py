# 整个项目共同使用的固定设置表。
import pandas as pd

#从 src 文件夹里的 extract.py 文件中，拿一些东西过来。
from src.extract import (
    extract_path,
    extract_signal_data,
    flow_datail_df,
    flow_summary_df,
    excel_files
)

from src.quality import check_all, standardize_numbers
from pathlib import Path

"""函数自动化提取20路口表并合并"""

signal_list = []       # 合并信号配时数据
flow_detail_list = []  # 合并15分钟流量数据
flow_summary_list = [] # 合并转向比例 + 总流量汇总表

# 让路口编号分别调用 1-20
for intersection in range(1,21):

    # 调用 extract_path 获取目标路口路径
    file_path = extract_path(excel_files, intersection)

    # # 验证1：打印当前处理的是哪个文件
    # print("准备处理路口：", intersection)
    # print("当前文件路径：", file_path)
    #
    # # 验证2：查看这个Excel里面有哪些Sheet
    # print("Sheet名称：", pd.ExcelFile(file_path).sheet_names)

    # 调用三个提取函数  append
    signal_list.append(
        extract_signal_data(file_path, intersection)
    )

    flow_detail_list.append(
        flow_datail_df(file_path, intersection)
    )

    flow_summary_list.append(
        flow_summary_df(file_path, intersection)
    )
    # print("正在处理路口：", intersection)

# 数据拼接，整理成 整表形式
signal_all_df = pd.concat(signal_list,axis=0,ignore_index=True)

flow_detail_all_df = pd.concat(flow_detail_list,axis=0,ignore_index=True)

flow_summary_all_df = pd.concat(flow_summary_list,axis=0,ignore_index=True)


# print(signal_all_df)
# print(flow_detail_all_df)
# print(flow_summary_all_df)
#
# print("信号配时：", signal_all_df.shape)
# print("流量明细：", flow_detail_all_df.shape)
# print("流量汇总：", flow_summary_all_df.shape)

signal_all_df.to_csv(
    "output/staging/signal_all.csv",
    index=False,
    encoding="utf-8-sig"
)
flow_detail_all_df.to_csv(
    "output/staging/flow_detail_all.csv",
    index=False,
    encoding="utf-8-sig"
)
flow_summary_all_df.to_csv(
    "output/staging/flow_summary_all.csv",
    index=False,
    encoding="utf-8-sig"
)


# 4. 数据质量检查
print("开始数据质量检查")

quality_report, missing_report = check_all(
    signal_all_df,
    flow_detail_all_df,
    flow_summary_all_df
)

# 5. 保存质量检查结果
quality_report.to_csv(
    "output/quality_report.csv",
    index=False,
    encoding="utf-8-sig"
)

missing_report.to_csv(
    "output/missing_report.csv",
    index=False,
    encoding="utf-8-sig"
)

# 6. 基础数据类型标准化
Path("output/processed").mkdir(parents=True, exist_ok=True)

tables = {
    "signal_all": signal_all_df,
    "flow_detail_all": flow_detail_all_df,
    "flow_summary_all": flow_summary_all_df
}

for name, df in tables.items():
    processed_df = standardize_numbers(df)

    processed_df.to_csv(
        f"output/processed/{name}.csv",
        index=False,
        encoding="utf-8-sig"
    )

print("质量检查完成")
print("发现待核实问题：", len(quality_report))
print("结果已导出到output文件夹")
