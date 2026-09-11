# 表7 模型参数与经验式汇总

> 所有取值来自题目附录与已确认的建模口径；恒温段环境为**人工设定口径**，非实测。

| 符号 | 含义 | 取值/经验式 | 单位 | 来源 |
|---|---|---|---|---|
| R0 / R_min | 药材初始/最终半径 | 2.000 / 1.198 | cm | 附件2（问题4） |
| L | 药材长度 | 25 | cm | 题目 |
| T0 | 初始温度 | 28 | °C | 题目 |
| C0 | 初始干基含水率 | 2.55 | kg/kg | 题目 |
| T_inf | 恒温段环境温度 | 50 | °C | g_framing_env_extrapolation（人工口径） |
| C_inf | 恒温段环境水分浓度 | 0.05 | kg/kg | g_framing_env_extrapolation（人工口径） |
| h | 对流换热系数 | 25 | W/(m²·K) | g_framing_convective_coefficients |
| h_m | 对流传质系数 | 8×10⁻⁷ | m/s | g_framing_convective_coefficients |
| ρ | 密度（附录2/3/4） | 820 / 650+128C / 760+90C | kg/m³ | 附录2/3/4 |
| c_p | 比热容（附录2/3/4） | 2600 / 1450+2736C/(C+1) / 1850+2150C/(C+1) | J/(kg·K) | 附录2/3/4 |
| k | 导热系数（附录2/3/4） | 0.36 / 0.21+0.38C/(C+1) / 0.12+0.20C/(C+1) | W/(m·K) | 附录2/3/4 |
| D | 水分扩散系数（附录2/3/4） | 7e-9·exp(-0.89/C) / 2.4e-3·exp(-0.45/C)·exp(-3850/T) / 4.2e-4·exp(-0.30/C)·exp(-3850/T) | m²/s | 附录2/3/4 |
| 判据 | 烘干完成判据 | 全域最大 C ≤ 0.15 | kg/kg | g_caliber_criterion_granularity / g_caliber_overall_indicator |
| 坐标口径 | 问题4 报告坐标 | 当前物理距离，r > R(t) 留空 (T1) | — | g_framing_q4_coordinate_caliber |
