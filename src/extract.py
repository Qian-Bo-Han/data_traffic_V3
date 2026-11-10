# =========================
# 1. 导入库
# =========================
import os
import glob
import pandas as pd
import numpy as np

#  数据提取
# 找到原始数据
# 1. 项目根目录                                              # base_dir = os.getcwd()  #获取“当前程序运行时的工作目录”。
base_dir = os.path.dirname(                                # __file__ = 当前 Python 文件的位置。
    os.path.dirname(os.path.abspath(__file__))             # os.path.abspath() 把路径变成完整的“绝对路径”。
)                                                          # os.path.dirname() 去掉最后一级，得到“它所在的文件夹”。

# 2. 原始数据文件夹
data_folder = os.path.join(base_dir,"data_traffic")        # os.path.join() 把几段路径安全地拼起来。
                                                           # data_folder 保存“原始数据文件夹”的完整路径。
# 3. 找到所有路口Excel
excel_files = glob.glob(                                   # glob.glob(...) 按照这个规则，去磁盘里找所有符合条件的文件。
    os.path.join(data_folder,"demo_*.xlsx")
)

# print("base_dir =", base_dir)
# print("data_folder =", data_folder)
# print("excel_files =", excel_files)

#---------------------------------------------------

# 3. 根据路口编号找文件

def extract_path(excel_files,intersection):  # 给我所有 Excel 路径 + 我想找的路口编号。

    #获取文件名
    for file_path in excel_files:
        # 1. 当前路径 → 文件名
        file_name = os.path.basename(file_path)

        # 2. 提取路口编号
        intersection_id = int(
            file_name.split("_")[1].split("流量")[0]
        )

         # 3. 判断是不是我要找的路口
        if intersection_id ==intersection:
            file_intersection_path = file_path

            return file_intersection_path
#检验
# file_1_path = extract_path(excel_files,1)
# print(file_1_path)


# =========================
# 4. 提取信号配时数据
# =========================

def extract_signal_data(file_path, intersection):

    #第一步：获取当前Excel所有的sheet名称
    excel_file = pd.ExcelFile(file_path)
    names = excel_file.sheet_names

    #第二步：选择实际存在的Sheet
    if "信号配时数据" in names:
        actual_sheet_name = "信号配时数据"

    elif "配信号时数据" in names:
        actual_sheet_name = "配信号时数据"
    else:
        raise ValueError(f"{intersection}号路口：找不到信号配时工作表")

    signal_raw_df = pd.read_excel(
        file_path,  # 去哪个Excel文件找
        sheet_name=actual_sheet_name,
        header=None  # 暂时不要把Excel某一行自动认作字段名，
        # 先把整张表原样读进来
    )  # 前面的括号，只是给 pd.read_excel() 这个函数传参数。
    # 只负责“怎么读取 Excel”。

    signal_df = signal_raw_df.iloc[2:14].copy()
    # 把表中真正数据提取出来了

    # 直接使用第一行作为表头
    signal_df.columns = signal_raw_df.iloc[1]

    # 删除没有相位编号的无效空白行
    signal_df = signal_df.dropna(subset=["相位编号"])

    # 向下填充
    signal_df[
        ["时段分类", "时段范围", "周期总时长(s)"]
    ] = signal_df[
        ["时段分类", "时段范围", "周期总时长(s)"]
    ].ffill()

    # 重置索引
    signal_df = signal_df.reset_index(drop=True)

    # 表头添加路口编号
    signal_df.insert(0, "路口编号", intersection)

    # 最终返回值
    return signal_df

#检验
# file_20_path = extract_path(excel_files,20)
# df_20 = extract_signal_data(file_20_path,20)
# print(df_20)

#-------------------------------------------------------------
# 自动化读取 流量数据”Sheet”

# 1：15分钟流量明细表 ：flow_detail_df
    # 通过iloc读取1-11，等数据，导入，拼接，给字段命名导出，
    # iloc分别读取总流量，转向比例，命名，导出，拼接
    # 动态化提取相应数据（根据函数名）

def flow_datail_df(file_path, intersection_id):
    signal_raw_df = pd.read_excel(file_path, sheet_name="流量数据", header=None)

    # 先找出 总流量的行数
    total_rows = signal_raw_df.index[
        signal_raw_df.iloc[:,1] == "总流量"      # 取所有行，第 2 列 判断
        ].tolist()                              #把 Series 转成普通列表，只保留里面的数据值。

    # 载体 对应早中晚路口行
    morning_total_row = total_rows[0]
    offpeak_total_row = total_rows[1]
    evening_total_row = total_rows[2]

    # 拼接整理字段名
    # 分别提取表中第一行，第二行
    row_1 = signal_raw_df.iloc[1].ffill()
    row_2 = signal_raw_df.iloc[2]

    # 拼接
    turn = row_2.str.replace("(pcu)","")
    flow_columns = row_1+turn+"流量"

    # 将 第1，2行数据替换
    flow_columns.iloc[0:2] = ["统计开始时间", "统计结束时间"]

    morning_df = signal_raw_df.iloc[morning_total_row-8 : morning_total_row ].copy()
    morning_df.columns = flow_columns
    morning_df.insert(0, "路口编号", intersection_id)
    morning_df.insert(1, "时段分类", "早高峰")
    morning_df = morning_df.reset_index(drop=True)

    offpeak_df = signal_raw_df.iloc[offpeak_total_row-8 : offpeak_total_row].copy()
    offpeak_df.columns = flow_columns
    offpeak_df.insert(0, "路口编号", intersection_id)
    offpeak_df.insert(1, "时段分类", "平峰")
    offpeak_df = offpeak_df.reset_index(drop=True)

    evening_df = signal_raw_df.iloc[evening_total_row-8 : evening_total_row].copy()
    evening_df.columns = flow_columns
    evening_df.insert(0, "路口编号", intersection_id)
    evening_df.insert(1, "时段分类", "晚高峰")
    evening_df = evening_df.reset_index(drop=True)

    # 拼接数据
    flow_raw_df = pd.concat([morning_df, offpeak_df, evening_df], axis=0, ignore_index=True)

    return flow_raw_df
# # 检验
# file_2_path = extract_path(excel_files,2)
# df_2 = flow_datail_df(file_2_path,2)
# print(df_2)

#-----------------------------------------------------------
# 专门创建转向比例 + 总流量汇总表 ：flow_summary_df 函数：
# 总流量：11，26，41 转向比例：12，27，42
def flow_summary_df(file_path, intersection_id):

    # 1. 读取原始Excel
    signal_raw_df = pd.read_excel(file_path, sheet_name="流量数据", header=None)

    # 2. 定位三个时段的总流量行

    # 先找出总流量的行数
    total_rows = signal_raw_df.index[
        signal_raw_df.iloc[:, 1] == "总流量"  # 取所有行，第二列判断
        ].tolist()

    # 载体 对应早中晚路口行
    morning_total_row = total_rows[0]
    offpeak_total_row = total_rows[1]
    evening_total_row = total_rows[2]

    # 3.动态识别进口名称和位置

    # 自动提取合并列名

    row_1 = signal_raw_df.iloc[1].ffill()
    row_2 = signal_raw_df.iloc[2].str.replace("(pcu)", "")

    # 4. 提取三个时段的进口总流量

    # 去重，保留每个进口第一次出现的位置
    ports = row_1.drop_duplicates()

    # 只保留带有“进口”的字段
    ports = ports[
        ports.astype("string").str.contains("进口", na=False)
    ]

    # 获取总流量列位置
    summary_positions = ports.index.tolist()

    # 生成总流量字段名称
    summary_columns = (ports + "总流量").tolist()

    # 根据行位置，列位置提取实时数据
    liuliang = signal_raw_df.iloc[total_rows, summary_positions].copy()

    # 给提取出来的数据命名（总流量数据完成）
    liuliang.columns = summary_columns

    # 5. 提取三个时段的转向比例

    # 获取原始转向字段表头
    turn_header = signal_raw_df.iloc[2]

    # 筛选包含pcu的转向字段
    turn_fields = turn_header[
        turn_header.astype("string").str.contains("pcu", na=False)
    ]

    # 获取转向比例列位置
    ratio_positions = turn_fields.index.tolist()

    # 进口转向比例字段名字
    ratio_columns = (row_1 + row_2).iloc[ratio_positions] + "比例"

    # 早高峰
    morning_ratio = signal_raw_df.iloc[morning_total_row + 1:morning_total_row + 2, ratio_positions].copy()
    morning_ratio.columns = ratio_columns
    # 平峰
    offpeak_ratio = signal_raw_df.iloc[offpeak_total_row + 1:offpeak_total_row + 2, ratio_positions].copy()
    offpeak_ratio.columns = ratio_columns
    # 晚高峰
    evening_ratio = signal_raw_df.iloc[evening_total_row + 1:evening_total_row + 2, ratio_positions].copy()
    evening_ratio.columns = ratio_columns


    # 6.重置索引并横向合并

    # 重置流量表索引
    liuliang = liuliang.reset_index(drop=True)

    flow_ratio_df = pd.concat(
        [morning_ratio, offpeak_ratio, evening_ratio
         ], axis=0, ignore_index=True)
    # print(flow_ratio_df)

    # 在最终横向拼接
    flow_summary_ratio_df = pd.concat([liuliang, flow_ratio_df], axis=1)

    flow_summary_ratio_df.insert(
        0, "路口编号", intersection_id
    )

    flow_summary_ratio_df.insert(
        1, "时段分类", ["早高峰", "平峰", "晚高峰"]
    )

    return flow_summary_ratio_df


file_path = extract_path(excel_files, 8)

flow_raw_df = pd.read_excel(
    file_path,
    sheet_name="流量数据",
    header=None
)
# print(flow_raw_df)

total_rows = flow_raw_df.index[
    flow_raw_df.iloc[:,1] == "总流量"
].tolist()










