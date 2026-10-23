import fs from 'node:fs/promises';
import path from 'node:path';
import {finalizePresentation} from 'file:///C:/Users/Steven/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations/container_tools/artifact_tool_utils.mjs';
const ROOT='C:/courses/密码与网络安全引论';
const SKILL='C:/Users/Steven/.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations';
const finalPath=path.join(ROOT,'output/一笔成章 · 中期汇报 v1.2 蓝绿优化版.pptx');
const result=await finalizePresentation({
 workspaceDir:ROOT,
 candidatePath:path.join(ROOT,'.ppt-redesign/candidate.pptx'),
 finalPath,
 explicitTotalSlideCount:13,
 requiredNativeTableOwnerSlides:[5,7],
 requiredNativeChartOwnerSlides:[],
 pythonExecutable:'C:/Users/Steven/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
 integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit','--require-native-table-slide','5','--require-native-table-slide','7'],
 fontPolicy:{basis:'design',families:['Microsoft YaHei']},
 verifyArtifactToolImport:true,
 receiptPath:path.join(ROOT,'.ppt-redesign/final.validation.json')
});
console.log(JSON.stringify(result,null,2));
