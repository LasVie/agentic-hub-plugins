# 第三方许可与署名

离线乐谱工作台的独立排版引擎基于 Verovio 6.4.0。下列许可分别适用于所列第三方材料。许可原文、原作者署名和免责声明保留在各子目录。

## verovio

- 来源：https://github.com/rism-digital/verovio
- 固定版本：cb5fcfa1178238138aa7f51f1e55f6a743eb26cc
- 许可：LGPL-3.0-only
- 许可及原署名：`licenses/verovio/`
- 适用材料与权利人：Laurent Pugin 和其他作者。重建 C++ 排版引擎与浏览器模块。首选源码、修改说明与重建步骤见同目录。

## libmei

- 来源：https://github.com/rism-digital/libmei
- 固定版本：Verovio snapshot cb5fcfa1178238138aa7f51f1e55f6a743eb26cc
- 许可：MIT
- 许可及原署名：`licenses/libmei/`
- 适用材料与权利人：Andrew Hankinson、Alastair Porter 和其他作者。对应源码中的生成器与属性类。

## mei-schema

- 来源：https://github.com/music-encoding/music-encoding
- 固定版本：Verovio ODD snapshot cb5fcfa1178238138aa7f51f1e55f6a743eb26cc; MEI commit recorded inside libmei/mei/mei-commit.txt
- 许可：ECL-2.0
- 许可及原署名：`licenses/mei-schema/`
- 适用材料与权利人：音乐编码倡议（MEI）委员会和原文件署名作者。对应源码中的 ODD 生成输入。

## jsonxx

- 来源：https://github.com/hjiang/jsonxx
- 固定版本：Verovio snapshot cb5fcfa1178238138aa7f51f1e55f6a743eb26cc
- 许可：MIT
- 许可及原署名：`licenses/jsonxx/`
- 适用材料与权利人：Hong Jiang。引擎内嵌 JSON 解析代码。

## pugixml

- 来源：https://pugixml.org/
- 固定版本：1.16 as vendored in cb5fcfa1178238138aa7f51f1e55f6a743eb26cc
- 许可：MIT
- 许可及原署名：`licenses/pugixml/`
- 适用材料与权利人：Arseny Kapoulkine。引擎内嵌 XML 解析代码。

## midifile

- 来源：https://github.com/craigsapp/midifile
- 固定版本：Verovio snapshot cb5fcfa1178238138aa7f51f1e55f6a743eb26cc (January 2021 MidiFile header)
- 许可：BSD-2-Clause
- 许可及原署名：`licenses/midifile/`
- 适用材料与权利人：Craig Stuart Sapp。引擎内嵌 MIDI 读写代码。

## miniz-cpp

- 来源：https://github.com/kkzi/miniz-cpp
- 固定版本：62ec5c46c276d1880ba3b5a121d5a5dc24667b9e as adapted in Verovio
- 许可：MIT AND Unlicense
- 许可及原署名：`licenses/miniz-cpp/`
- 适用材料与权利人：Thomas Fussell、RAD Game Tools、Valve Software、Rich Geldreich、Tenacious Software LLC 和 Martin Raiber。引擎内嵌 ZIP 库。原文件中亦保留 Alex Evans 的公有领域 PNG 写入器注记。

## tuning-library

- 来源：https://github.com/surge-synthesizer/tuning-library
- 固定版本：Verovio snapshot cb5fcfa1178238138aa7f51f1e55f6a743eb26cc
- 许可：MIT
- 许可及原署名：`licenses/tuning-library/`
- 适用材料与权利人：Paul Walker。引擎内嵌调律库。

## crc

- 来源：https://barrgroup.com/blog/crc-series-part-3-crc-implementation-code-cc
- 固定版本：Verovio snapshot cb5fcfa1178238138aa7f51f1e55f6a743eb26cc
- 许可：LicenseRef-CRC-Public-Domain
- 许可及原署名：`licenses/crc/`
- 适用材料与权利人：Michael Barr。引擎内嵌 CRC 代码。原作者公有领域声明保留。

## base64

- 来源：https://renenyffenegger.ch/notes/development/Base64/Encoding-and-decoding-base-64-with-cpp
- 固定版本：Verovio snapshot cb5fcfa1178238138aa7f51f1e55f6a743eb26cc
- 许可：LicenseRef-Nyffenegger-Base64
- 许可及原署名：`licenses/base64/`
- 适用材料与权利人：René Nyffenegger。引擎内嵌 Base64 代码。原作者许可完整保留。

## leipzig

- 来源：https://github.com/rism-digital/leipzig
- 固定版本：5.2.102 as vendored in cb5fcfa1178238138aa7f51f1e55f6a743eb26cc
- 许可：OFL-1.1
- 许可及原署名：`licenses/leipzig/`
- 适用材料与权利人：Etienne Darbellay、Jean-Francois Marti、Laurent Pugin 和 Klaus Rettinghaus。保留上游字形轮廓与来源文件。未转换成另一个字体。

## bravura

- 来源：https://github.com/steinbergmedia/bravura
- 固定版本：Verovio snapshot cb5fcfa1178238138aa7f51f1e55f6a743eb26cc; original notice dated 2021
- 许可：OFL-1.1
- 许可及原署名：`licenses/bravura/`
- 适用材料与权利人：Steinberg Media Technologies GmbH、Daniel Spreadbury。保留上游字形轮廓与来源文件。未转换成另一个字体。

## liberation-fonts

- 来源：https://github.com/liberationfonts/liberation-fonts
- 固定版本：2.1.5; Debian fonts-liberation2_2.1.5-1_all.deb
- 许可：OFL-1.1
- 许可及原署名：`licenses/liberation-fonts/`
- 适用材料与权利人：Google Corporation 和 Red Hat。随对应源码分发的四个未修改的 Serif 字体文件仅用于重建文本度量。度量是 XML 数值表，浏览器不加载这些字体。

## emscripten

- 来源：https://github.com/emscripten-core/emscripten
- 固定版本：4.0.23 / 7a5d93b50f6a3a35e85a0d2fc9e667b8498e6aed
- 许可：MIT
- 许可及原署名：`licenses/emscripten/`
- 适用材料与权利人：Emscripten 作者。链接的运行时和生成的 JavaScript 接口使用 MIT 选项。保留上游完整双许可原文。

## musl

- 来源：https://musl.libc.org/
- 固定版本：Emscripten 4.0.23 sysroot snapshot
- 许可：MIT
- 许可及原署名：`licenses/musl/`
- 适用材料与权利人：Rich Felker 和其他贡献者。Emscripten 所附 musl 运行时。

## llvm-runtime

- 来源：https://github.com/llvm/llvm-project
- 固定版本：Emscripten 4.0.23 sysroot snapshots
- 许可：Apache-2.0 WITH LLVM-exception
- 许可及原署名：`licenses/llvm-runtime/`
- 适用材料与权利人：LLVM 贡献者。Emscripten 所附 libc++、libc++abi、compiler-rt 和 libunwind。

## dlmalloc

- 来源：https://gee.cs.oswego.edu/dl/html/malloc.html
- 固定版本：2.8.6 as included in Emscripten 4.0.23
- 许可：CC0-1.0
- 许可及原署名：`licenses/dlmalloc/`
- 适用材料与权利人：Doug Lea。Emscripten 所附内存分配器。原声明及其引用的 CC0 条款保留。

## 改动及重建

此引擎以本地 Emscripten 4.0.23 编译，编译时关闭 JavaScript 字符串动态执行。编译选项关闭 Humdrum、MXL、ABC、GABC、PAE，工作台不调用图形编辑接口。保留 Leipzig 与 Bravura 的字形资源，删除其他字形包、旧 Liberation Serif 1.04、嵌入 CSS 字体和页脚图像。以独立的 OFL Liberation Serif 2.1.5 生成新的文本度量。请参阅 `licenses/verovio/重建说明.md`。
