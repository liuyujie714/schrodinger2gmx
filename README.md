# ffld_gmx_top.py

将 Schrodinger 中的 `ffld_server` 工具输出的 OPLS_2005 力场参数转换为 GROMACS 的 `.itp` 和 `.top` 拓扑文件。

> ⚠️ **注意**：此脚本主要基于 AI 生成，使用时请注意核查转换结果的正确性

## 环境要求

- Python 3.6+

## 用法

```bash
python ffld_gmx_top.py <input.out>
```

| 参数        | 必需 | 说明                                |
| ----------- | ---- | ----------------------------------- |
| `input.out` | 是   | 输入 ffld_server 生成的力场参数文件 |

同时生成同名的 `input.itp`和`input.top` 文件。

### 示例

```bash
python ffld_gmx_top.py input.out
```

## 单位换算

| 项目       | 输入          | 输出                      |
| ---------- | ------------- | ------------------------- |
| σ          | Å             | nm (÷10)                  |
| ε          | kcal/mol      | kJ/mol (×4.184)           |
| 键 k       | kcal/mol/Å²   | kJ/mol/nm² (×2×4.184×100) |
| 键长 r0    | Å             | nm (÷10)                  |
| 角 k       | kcal/mol/rad² | kJ/mol/rad² (×2×4.184)    |
| 二面角     | kcal/mol      | kJ/mol (×4.184)           |
| 异常二面角 | kcal/mol      | kJ/mol (×4.184/2)         |

## 输出

- `*.itp`：含 `[ atomtypes ]`、`[ moleculetype ]`、`[ atoms ]`、`[ bonds ]`、`[ angles ]`、`[ dihedrals ]`、`[ pairs ]`
- `*.top`：含 `[ defaults ]`、`#include`、`[ system ]`、`[ molecules ]`，可直接用于 GROMACS

## 可调参数

编辑脚本 `main()` 中：

```python
molecule_name = "UNK"    # 分子名
type_prefix   = "mm_"    # 原子类型前缀
```

# 注意

- 元素符号无法识别时默认按碳处理

