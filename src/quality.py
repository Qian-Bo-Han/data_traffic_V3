
import pandas as pd

PERIODS = ["早高峰", "平峰", "晚高峰"]
KEYS = ["路口编号", "时段分类"]


def check_all(signal_df, detail_df, summary_df):
    issues = []
    missing = []

    tables = [
        ("信号配时", signal_df, None),
        ("流量明细", detail_df, 8),
        ("流量汇总", summary_df, 1)
    ]

    # 1. 基础结构、重复、缺失、数值检查
    for name, df, expected_count in tables:

        print(f"{name}：{df.shape[0]}行，{df.shape[1]}列")

        duplicates = df.duplicated().sum()
        print("完全重复行数：", duplicates)

        if duplicates:
            issues.append([name, "全表", f"完全重复{duplicates}行"])

        # 检查20路口、三个时段的记录数量
        counts = df.groupby(KEYS).size()

        for route in range(1, 21):
            for period in PERIODS:
                count = int(counts.get((route, period), 0))

                # 信号相位数量不固定，但应有记录
                if expected_count is None:
                    abnormal = count == 0
                else:
                    abnormal = count != expected_count

                if abnormal:
                    issues.append([
                        name, f"{route}号/{period}",
                        f"记录数为{count}，需要核对"
                    ])

        # 记录缺失值，不直接填0
        for col, count in df.isna().sum().items():
            if count:
                missing.append([name, col, int(count)])

        # 检查数值转换、负数和比例范围
        for col in df.columns:
            if not any(x in col for x in ("流量", "比例", "时长")):
                continue

            values = pd.to_numeric(df[col], errors="coerce")
            invalid = (df[col].notna() & values.isna()).sum()
            negative = (values < 0).sum()

            if invalid:
                issues.append([name, col, f"{invalid}个非数值"])

            if negative:
                issues.append([name, col, f"{negative}个负数"])

            if "比例" in col and (values > 1).any():
                issues.append([name, col, "存在大于1的比例，需核对单位"])

    # 2. 检查流量明细与汇总是否一致
    directions = [
        "东", "西", "北", "南",
        "东北", "西南", "东南", "西北"
    ]

    for direction in directions:
        total_col = f"{direction}进口总流量"
        turn_cols = [
            f"{direction}进口{turn}流量"
            for turn in ("左转", "直行", "右转")
        ]

        if total_col not in summary_df.columns:
            continue

        if any(c not in detail_df.columns for c in turn_cols):
            continue

        temp = detail_df[KEYS + turn_cols].copy()

        for col in turn_cols:
            temp[col] = pd.to_numeric(temp[col], errors="coerce")

        grouped = temp.groupby(KEYS)[turn_cols]

        detail_total = grouped.sum(min_count=1).sum(
            axis=1, min_count=1
        )

        # 三种转向的8条记录齐全时才比较
        complete = grouped.count().min(axis=1).eq(8)

        summary_total = pd.to_numeric(
            summary_df.set_index(KEYS)[total_col],
            errors="coerce"
        )

        comparison = pd.concat([
            detail_total.rename("明细"),
            summary_total.rename("汇总"),
            complete.rename("可比")
        ], axis=1).dropna(subset=["明细", "汇总"])

        for (route, period), row in comparison.iterrows():
            if row["可比"] and abs(row["明细"] - row["汇总"]) > 1:
                issues.append([
                    "流量一致性",
                    f"{route}号/{period}/{direction}进口",
                    f"明细合计{row['明细']:g}，"
                    f"汇总{row['汇总']:g}，待核实"
                ])

    issue_df = pd.DataFrame(
        issues, columns=["检查表", "位置或字段", "问题"]
    )

    missing_df = pd.DataFrame(
        missing, columns=["检查表", "字段", "缺失数量"]
    )

    return issue_df, missing_df


# 3. 基础数值类型标准化
def standardize_numbers(df):
    result = df.copy()

    for col in result.columns:
        if any(x in col for x in ("流量", "比例", "时长")):
            result[col] = pd.to_numeric(
                result[col], errors="coerce"
            )

    return result










