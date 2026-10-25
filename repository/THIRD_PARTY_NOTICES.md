# 代码、数据与第三方权利

本地候选仓库，未上传。根目录 LICENSE_CODE 沿用原资源包的范围：只覆盖明示的项目自身代码与自身纯函数副本，不把第三方实现、权重或数据重新许可为 MIT。派生标签和数值示例见 DATA_LICENSE；原 MOT20 署名见 core/ATTRIBUTION.md。

|组件|仓库位置|处理|
|---|---|---|
|ByteTrack / YOLOX 检测模型代码|src/detect/frozen/r15_yolox82e_vendor|保留已批准适配副本的 Megvii 版权头、NOTICE.md 与 LICENSE.ByteTrack；来源固定提交和既有导入迁移见其说明|
|作者 ByteTrack / OC-SORT / BoT-SORT 适配|src/track/frozen/sota83d/vendor|各目录保留上游 LICENSE 与源文件版权头；既有NumPy/私有导入兼容改动作为历史适配披露|
|SORT 衍生代码署名|src/track/frozen/sota83d/vendor/oc/ocsort.py|保留源文件对原作者的署名与联系信息；这是第三方来源署名，不是本项目用户个人信息|
|Ultralytics、Torch、NumPy、SciPy、LAP、FilterPy、OpenCV|由使用者单独取得|不把外部依赖整包复制进仓库；依赖继续受各自许可约束，项目的MIT不替代它们|
|人工核验模板|review/|只含项目模板与合成测试；没有素材、正式样本清单或真实答案|

本仓库复制的是已经执行过的适配版本，不宣称与上游完整仓库逐文件相同。FROZEN_CODE_MAP区分原项目完整文件副本、原样科学节点切片和新增路径适配；完整文件的原项目SHA不是上游签名。冻结代码中的第三方版权/许可声明不能为了匿名而删去。

上游软件许可证与模型权重许可是不同问题。权重地址与本地取得版本SHA见 DATA.md；权重不分发。公开发布前仍需最终贡献归属、依赖权利链和署名复核；本地可运行与持有许可证文件本身不替代该项验收。

