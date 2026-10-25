# PHUC STUDIO — Website quảng bá sản phẩm

Đinh Hữu Phúc · DTC255180105 · KTPM K23B · Giảng viên Hoàng Văn Tâm.

WordPress/MySQL phục vụ danh mục, chi tiết và quản trị sản phẩm. Giao diện dùng cùng phông Be Vietnam Pro hỗ trợ tiếng Việt và ảnh thiết bị thật được lưu local. Source/cấu hình/tài nguyên ứng dụng trên GitHub; Word và ảnh minh chứng ở ngoài repository.

## Một file Compose

Browser → Nginx:8082 → WordPress → MySQL. Prometheus lấy metrics từ cAdvisor, Nginx exporter và MySQL exporter; Grafana hiển thị dashboard. Nginx access/WordPress audit → Promtail → Loki → Grafana Explore.

`docker-compose.yml` là file Compose duy nhất, không profiles, override hay wrapper ghép `-f`. Cấu hình riêng ở `nginx/`, `monitoring/`, `logging/`; theme/plugin ở `app/`.

Ba tác vụ `init-logs`, `database-init`, `wordpress-init` chuẩn bị quyền log, tài khoản exporter và dữ liệu web rồi thoát mã 0. Mười một dịch vụ dài hạn tiếp tục chạy. `database-init` dùng Unix socket chung với MySQL, không có mạng. Khởi tạo chạy lại không xóa dữ liệu hiện có.

## Chạy trên Ubuntu

Yêu cầu Docker Engine, Compose plugin, Git, Python 3. Máy lab dùng Ubuntu 26.04.1 LTS, 2 vCPU, RAM Linux khoảng 1,6 GiB và swap 2 GiB; khuyến nghị 4 GB RAM. Không thay Engine trong VM bằng Docker Desktop trên Windows.

```bash
git clone https://github.com/Phucdz2112/Web_QC_sanpham
cd Web_QC_sanpham
python3 scripts/create-env.py
```

Sửa `BIND_IP` theo IP VM. Script sinh mật khẩu riêng trong `.env` mode 600, không in mật khẩu hoặc ghi đè file cũ. `.env.example` liệt kê đúng các biến được dùng: IP, cổng, DB/user và tài khoản quản trị.

```bash
sudo docker compose config --quiet
sudo docker compose up -d --build
sudo docker compose ps -a
```

Một lệnh `up` khởi động toàn bộ stack sau khi chuẩn bị `.env`; không cần cài web/exporter bằng script riêng. Chờ các healthcheck và ba init thoát 0, rồi kiểm tra API/giao diện. Grafana có thể cần thêm thời gian khởi động.

Máy bàn giao dùng `/home/phuc2102/Project`, tên Compose `project`. Giữ volume `project_wordpress_data`, `project_mysql84_data` và các volume quan sát. Đổi project name tạo bộ volume khác; không dùng `down -v` hoặc prune volumes.

## Truy cập và tài khoản

Website http://192.168.74.141:8082 ; quản trị `/wp-admin/`. URL WordPress tự suy ra từ `BIND_IP` và `WEB_PORT`.

**PowerShell trên Windows**, giữ SSH tunnel:

```powershell
ssh -N -L 5432:127.0.0.1:5432 -L 3002:127.0.0.1:3002 -L 9091:127.0.0.1:9091 -L 3101:127.0.0.1:3101 phuc2102@192.168.74.141
```

| Thành phần | Địa chỉ trên Windows | User mặc định | Mật khẩu trong `.env` trên VM |
|---|---|---|---|
| WordPress | Website `/wp-admin/` | DTC255180105 | WP_ADMIN_PASSWORD |
| phpMyAdmin | http://localhost:5432 | wordpress | WORDPRESS_DB_PASSWORD |
| Grafana | http://localhost:3002 | DTC255180105 | GRAFANA_ADMIN_PASSWORD |
| Prometheus | http://localhost:9091 | Qua tunnel | Không bật auth riêng trong lab |
| Loki | http://localhost:3101 | Qua tunnel | Không bật auth riêng trong lab |

Không dùng root cho app. Không gửi `.env`, chụp mật khẩu hay in toàn bộ `docker compose config`. Đổi mật khẩu/tên DB/user hoặc tài khoản Grafana trên volume cũ cần backup và cập nhật SQL/tài khoản thật; chỉ thay environment không đổi dữ liệu đã lưu. Không xóa volume để làm nhanh.

## Giao diện và nghiệp vụ

Custom post type `product` lưu tên, nội dung, giá nguyên không âm và kiểu ảnh. Admin thêm/sửa/xóa/xuất bản; nonce và phân quyền bảo vệ thao tác ghi. Sáu sản phẩm mẫu được tạo một lần; không có thanh toán hay gửi thư thật. Tên bộ sưu tập và giá phục vụ đồ án.

Ảnh thật trong `app/theme/assets/photos/` là tài nguyên ứng dụng được commit cùng `sources.json`; không phải ảnh minh chứng. Phông local kèm giấy phép OFL. Xem [nguồn ảnh và phông](app/theme/assets/PHOTOS.md).

## Monitoring và logging

Grafana provision Prometheus/Loki và dashboard 10 panel UID `web-qc-system`, folder DTC255180105. Trong Prometheus kiểm tra `up`, `nginx_up`, `mysql_up`, `count(container_last_seen{name!=""})`. Hai metric dịch vụ phải bằng 1; exporter UP chưa đủ chứng minh DB/web kết nối được.

CPU là phần trăm một lõi, có thể vượt 100% trên nhiều vCPU. RAM dùng bytes; network rate có thể đếm trùng interface. Tạo traffic, chờ ít nhất hai lần scrape trước khi xem rate.

Trong Grafana Explore chọn Loki và thời gian gần nhất, chạy ba query trong `logging/queries.logql`. Truy cập web, URL lỗi hoặc thao tác sản phẩm thử để tạo log thật. Promtail đọc shared volumes chỉ đọc và giữ positions trên volume; log không ghi mật khẩu, cookie, token, body hay query string.

Promtail đã EOL 02/03/2026; giữ theo đề trong lab, sản xuất cần Alloy: https://grafana.com/docs/loki/latest/send-data/promtail/

## Hardening

Nginx UID 101, Prometheus/exporters 65534, Grafana 472, Loki 10001. Dịch vụ phù hợp dùng read_only, cap_drop và no-new-privileges. Tách frontend/backend internal/admin/monitoring; DB/exporters không publish; admin loopback. Mật khẩu riêng, .env 600; app user giới hạn schema; exporter account riêng. Nginx có bốn headers, ẩn version, chặn dotfiles/XML-RPC, rate limit login. WordPress tắt sửa file, kiểm tra nonce/quyền và escape đầu ra. Docker logs giới hạn 5 MB × 3 file.

Ngoại lệ: init chuẩn bị quyền/config; MySQL entrypoint hạ quyền; Apache master root rồi worker www-data; Promtail root đọc log nhưng drop capabilities/read-only; cAdvisor privileged đọc host. Không tuyên bố mọi container non-root. UFW được kiểm tra theo trạng thái thật; loopback không có nghĩa UFW đã bật. Người có quyền Docker có thể đọc bí mật container.

HTTP kèm headers đáp ứng lựa chọn của đề; chỉ demo mạng VM tin cậy. Headers không mã hóa mật khẩu; admin qua SSH tunnel. Không bật HSTS trên HTTP; sản xuất cần TLS. Grafana giới hạn 512 MB; VM ít RAM có thể dùng swap.

## Backup kiểm thử và demo

```bash
sudo python3 scripts/backup.py /home/phuc2102/web-qc-artifacts/backups
sudo env EVIDENCE_DIR=/home/phuc2102/web-qc-artifacts/evidence python3 tests/check.py
```

`check.py` kiểm tra runtime/API/UID/ports/networks và LogQL. `runtime.py` restore SQL vào schema riêng, dọn schema thử và đối chiếu digest sản phẩm sau restart. Không chạy restart/CRUD trên production khi chưa có backup.

```bash
npm install
npx playwright install chromium
EVIDENCE_DIR=/home/phuc2102/web-qc-artifacts/evidence npm run test:browser
```

Browser test tạo/sửa/xóa sản phẩm thử, kiểm tra font/ảnh, đăng nhập công cụ và chụp ảnh thật. Có thể đặt `BROWSER_EXECUTABLE` hoặc URL tunnel; ảnh minh chứng Linux được thu bằng headless trong VM. Mọi đầu ra nằm ngoài repo.

Xem [DEMO.md](DEMO.md) để đổi cổng rồi trả về, sửa app/Nginx/scrape interval/LogQL, phân biệt restart/recreate/build và dừng không xóa dữ liệu.

## Git và bàn giao

Giữ ba commit mốc app/DB/Nginx, monitoring, logging và lịch sử đã có; các commit sau hợp nhất Compose và hoàn thiện giao diện. Không viết lại lịch sử để giả tiến độ. Repo chỉ chứa source, cấu hình, tài nguyên ứng dụng, scripts, tests và tài liệu kỹ thuật. Word/PDF, minh chứng, render, dump và secrets ở ngoài repo.

## Kịch bản demo

Mở website và một trang chi tiết; đăng nhập WordPress bằng mã SV và thao tác sản phẩm; mở phpMyAdmin kiểm tra bảng; mở Prometheus Targets và hai metric availability; mở dashboard Grafana; chạy ba LogQL với log mới; trình bày networks, cổng, UID, headers, quyền DB và cách bảo vệ secrets; cuối cùng mở GitHub để đối chiếu commits và README.
