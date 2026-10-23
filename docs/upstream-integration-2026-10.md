# Tích hợp upstream ngày 23/10/2026

## Nguồn và phạm vi

- Repo gốc: [zzh20188/GKI_KernelSU_SUSFS](https://github.com/zzh20188/GKI_KernelSU_SUSFS).
- Nhánh `upstream/dev`, commit [ed9ca42709dfb23eae6034d67482d1c35631b85e](https://github.com/zzh20188/GKI_KernelSU_SUSFS/commit/ed9ca42709dfb23eae6034d67482d1c35631b85e).
- Nền fork trước khi tích hợp: `origin/dev` tại `8d86caf`. Nhánh local được fast-forward từ `437dfdb` trước khi merge upstream.
- Đồng bộ workflow, script SUSFS, stock config, dữ liệu kernel, tài liệu và giao diện danh mục mới từ upstream.
- Không thay đổi repo bot `build-kernel`, không sửa token/env, không push, không dispatch Actions hoặc flash thiết bị.

## Những thay đổi đáng chú ý từ upstream

- BakaSU thay thế tên ReSukiSU; thêm SukiSU(40726), SukiSU(40548) với cấu hình commit cố định.
- Chế độ `ksu_mode`: `关闭` = bật KSU và SUSFS; `禁用SUSFS` = chỉ bật KSU; `禁用KSU` = kernel không tích hợp cả hai.
- Tùy chọn NoMount, networking, NTSync và bộ patch CVE-2026-43499. Patch CVE vẫn tắt mặc định như upstream; việc nhập source không phải xác nhận hiệu quả bảo mật của patch.
- Retry clone/sync, xử lý branch Android bị deprecated hoặc chuyển thành tag, cập nhật tương thích SUSFS và cấu hình stock/LTO.
- Xuất log build, patch SUSFS tùy chọn; chọn Manager theo phiên bản KSU thay vì tải APK mới nhất không kiểm tra.
- Lịch cập nhật upstream chuyển sang ngày 1 và 16 hằng tháng. Auto Trigger vẫn có giới hạn owner upstream; không tự bật build định kỳ trên fork.

## Phần tương thích riêng của fork

| Input/cơ chế | Hành vi sau tích hợp |
| --- | --- |
| `kernelsu_variant=ReSukiSU` | Alias sang **BakaSU**, dùng repo Baka-SU/BakaSU; không checkout lại source ReSukiSU cũ. |
| `kernelsu_variant=KittiSU` | Giữ đường build, hỗ trợ SUSFS/KPM và tải Manager từ terebiko/KittiSU. |
| `kernelsu_branch` | Chấp nhận payload bot cũ nhưng không còn điều khiển branch. Theo chính sách upstream và commit trong `config/`. |
| `cancel_susfs=true` | Tắt SUSFS, giữ KSU; `ksu_mode=禁用KSU` luôn được ưu tiên cao hơn. |
| `use_kpm="true"` / `"false"` | Chấp nhận chuỗi boolean bot gửi, bên cạnh các nhãn upstream. `true` thực sự đi vào nhánh bật CONFIG_KPM trên biến thể hỗ trợ. |
| `artifact_upload_mode=all` | Upload toàn bộ như `上传全部`. |
| `artifact_upload_mode=anykernel` | Chỉ gói AnyKernel3 như `仅上传 AnyKernel3.zip`. |
| `sub_levels` ở main/workflow từng kernel | Danh sách số hoặc `X`, phân cách bằng dấu phẩy. Loại bản trùng và giữ thứ tự chọn; bản không tồn tại làm job lỗi, không fallback build toàn bộ. |
| `sub_level`, `revision`, `android_version` ở custom | Chấp nhận payload `/gki` và `/buildsave` cũ; kiểm tra kernel/sublevel/Android khớp nhau. Revision chỉ nhận `r` + chữ số. |

`sub_levels` để trống vẫn dùng **đúng matrix mặc định của upstream**, không tự thêm mọi bản có trong JSON. Khi chỉ định một sublevel mới ngoài matrix nhưng đã có trong `data/`, script lấy ngày phát hành mới nhất của sublevel đó, revision `r1`. Những hàng đã có trong matrix vẫn giữ ngày và revision gốc (đặc biệt Android 12).

**MKSU chưa được hỗ trợ:** bot hiện liệt kê MKSU trong menu, nhưng cả nền fork `8d86caf` lẫn upstream tích hợp đều chưa có nhánh setup/build cho nó. Bản tích hợp này không thêm lựa chọn MKSU vào Actions và không tự map sang một biến thể khác. Dùng SukiSU, ReSukiSU/BakaSU, KittiSU hoặc Official với bot hiện tại; muốn thêm MKSU cần chọn rõ nguồn và cơ chế tích hợp riêng.

Nếu gọi main với nhiều dòng kernel cùng lúc, danh sách `sub_levels` phải hợp lệ cho từng dòng được chọn. Muốn chọn riêng các sublevel khác nhau giữa các dòng, nên dispatch riêng từng dòng.

Giữ giá trị LTS mới hơn của fork: `5.10.270` và `6.12.96`. **Build LTS/X của 6.12 vẫn bị chặn** theo upstream; dữ liệu LTS không đồng nghĩa workflow đã hỗ trợ. Với 6.12, chọn bản có ngày phát hành cụ thể.

Các job vẫn dùng `ubuntu-24.04` GitHub-hosted. Không ép sang self-hosted. Bước dọn ổ được chặn trên runner persistent/self-hosted; bỏ apt chạy nền tranh lock với cài dependencies. Chưa cấu hình chạy kernel build trên VPS của bot.

## Sửa lỗi bổ sung

- Bỏ concurrency chung có thể hủy lượt build của người khác.
- Sửa khai báo input và GitHub context không hợp lệ mà actionlint phát hiện trong upstream.
- Dùng biến môi trường cho tên kernel/thời gian do người dùng nhập, tránh đưa trực tiếp thành mã shell. Tên kernel chỉ cho chữ ASCII, số, `.`, `_`, `+`, `-`, tối đa 64 ký tự.
- Kiểm tra cả `os_patch_level` lẫn sublevel mong đợi; từ chối build nhầm phiên bản. Custom chuyển tiếp giá trị đã chuẩn hóa.
- Giữ tên KittiSU, commit SukiSU cố định và nguồn SUSFS tương ứng trong release metadata. Release không coi build đã chọn nhưng bị skipped là thành công.
- Release trên fork vẫn sử dụng được khi chọn `Release`/`Pre-Release`; mặc định `Actions` không tạo release.

Không chạy lại `tools/sync_and_patch.py` cũ trong repo bot lên bộ workflow này: script đó giả định matrix tĩnh và có thể ép self-hosted hoặc thêm input vào reusable workflow không còn phù hợp. Tương thích bot đã nằm trực tiếp trong source fork.

## Ví dụ build một bản để kiểm tra

Sau khi review, commit/push lên nhánh muốn dùng, vào Actions → workflow custom (`kernel-custom.yml`) và chọn:

```json
{
  "kernel_version": "6.1",
  "os_patch_level": "2023-10",
  "sub_level": "25",
  "kernelsu_variant": "BakaSU",
  "cancel_susfs": false,
  "use_kpm": "false",
  "artifact_upload_mode": "all"
}
```

Đây chỉ là ví dụ payload kiểm tra pipeline, không phải khuyến nghị flash kernel 6.1.25 lên thiết bị bất kỳ. Cần chọn Android/KMI/patch level phù hợp thiết bị trước khi flash. Các input không ghi trong ví dụ dùng default của workflow custom; main có default khác, cần kiểm tra các toggle khi dispatch.

Bot phải trỏ `GKI_REPO` và nhánh build tới fork/nhánh đã push. Không cần thêm biến môi trường bot cho các alias trên. Tùy chọn upstream mới có thể chọn trực tiếp qua Actions; giao diện bot hiện chưa được sửa để hiển thị tất cả tùy chọn mới.

## Kiểm tra đã thực hiện và giới hạn

- actionlint cho toàn bộ workflow, kiểm tra trùng khóa YAML và hợp đồng input giữa các reusable workflow.
- 18 bài test offline ở `tests/test_upstream_integration.py`: matrix so với upstream, mọi ngày trong catalog, LTS, revision, input sai, xử lý chuỗi có ký tự shell và tên trường trong các payload thực tế của bot kế bên. Việc khớp tên trường không đồng nghĩa hỗ trợ MKSU.
- `bash -n` cho 95 khối shell script/các bước Bash trong workflow; Ruff cho script resolver/test mới.
- `npm ci --ignore-scripts` và `npm run build` cho web mới.

`tests/`, cache, `node_modules/` và `web/dist/` được gitignore; test là công cụ kiểm chứng local, không được đưa vào source deploy. Resolver runtime `scripts/workflow_inputs.py` là source cần commit.

Chưa chạy compile kernel trên GitHub Actions và chưa boot/flash kiểm thử. Các branch remote không pin commit vẫn có thể thay đổi giữa lúc build kernel và lấy Manager/metadata; kiểm tra commit thực tế trong log khi phát hành. Giữ nhánh main build theo upstream không có nghĩa mọi tổ hợp tính năng/kernel đều đã được kiểm chứng.
