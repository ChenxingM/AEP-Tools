"""示例：修改 .aep 文件中的合成名、图层名和属性值，然后另存为新文件。

用法:
    python examples/modify_project.py input.aep output.aep
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

from aep_tools import Project


def main():
    input_aep = Path(r"C:\Users\cmp094\Desktop\MHYA2_238_V1.aep")
    output_aep = Path(r"C:\Users\cmp094\Desktop\MHYA2_238_V1_2.aep")
    proj = Project.open(input_aep)

    for comp in proj.compositions:
        if comp.name == "_LO_238":
            layer = comp.layers[1]
            layer.name = "写入图层名"

            break

    proj.save(output_aep)
    print(f"已保存到: {output_aep}")


if __name__ == "__main__":
    main()
