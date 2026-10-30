# OcularSpan Windows 使用指南

软件 v0.3.0；测量模型仍为锁定 V5。Biometry Research 表示“生物测量研究”。这是独立科研工具，非厂家官方产品，不用于临床诊断。

## 下载与启动

从 [本项目 Releases](https://github.com/bzpb1998/OcularSpan/releases/latest) 下载 OcularSpan-v0.3.0-windows-x64.zip，完整解压，双击 OcularSpan.exe。保留 _internal、THIRD_PARTY_LICENSES 及随附文档。无需安装 Python 或 Conda，不启动浏览器或本地服务器。

当前程序无商业代码签名，Windows 可能提示未知发布者；请核对来源和 SHA-256，遵守所在单位的安全政策，不要关闭系统安全功能。

## 三步处理

1. 选择或拖入原始 ESX；也可选择文件夹，只读取当前层，不递归。优先使用未手工调整的原始导出文件。
2. 点击“开始分析”。文件在本机只读处理，不上传；可取消任务。单个文件失败不会丢弃其他有效文件的结果。
3. 点击“保存 Excel”，自行选择位置和文件名；默认按时间命名。关闭窗口即可退出。

没有 before/after 接口，不进行组间比较或眼轴增长统计。同一路径重复添加不会重复分析；不同文件的同一动物编号会保留为不同记录并加后缀。

## 文件权限

只需输入文件读取权限与输出目录写入权限。不需要管理员权限、EyeSuite 账号或 MySQL SELECT 权限。不连接或修改仪器数据库，不必安装到仪器电脑。请保存原始备份，确认已有 Excel 的覆盖提示后再保存。

## 输出与复核

只有“测量数据”“说明”两表；一只动物一行，OD/OS 中间两列空白。AL、CCT、AD、LT、RT 顺序固定；AL/AD/LT 单位 mm，CCT/RT 为 μm。晶体未通过门控时 AD/LT 留空，眼轴建议复核时数值保留并在说明页提示。质量标记不是准确概率。

AL 为角膜前表面至 ILM 的 EyeSuite 等效测量，AD 从角膜后表面起算；RT 仅作探索性参考。异常解剖和不清晰边界需要独立复核。软件更新名称和界面不改变模型，不代表已获得新的动物验证。

## 支持、引用与许可

问题提交到 [Issues](https://github.com/bzpb1998/OcularSpan/issues)。提供版本、操作步骤和匿名错误描述，不上传患者资料、原始研究 ESX、参考表或厂家软件；可用合成示例演示。

引用 Zhang J. OcularSpan. v0.3.0；无正式论文时不填写虚构 DOI。源码命令与环境见 REPRODUCIBILITY.md，模型限制见仓库 docs/V5_EXPERIMENTAL.md。

项目非厂家开发、认证或背书，软件按现状提供。完整范围和责任说明见 PROJECT_NOTICE.md、MIT LICENSE 和 THIRD_PARTY_NOTICES.md。
