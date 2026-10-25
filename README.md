# Website quảng bá sản phẩm bằng WordPress

**Đinh Hữu Phúc · DTC255180105 · KTPM K23B**  
Học phần Triển khai và quản trị hệ thống phần mềm. Repository: https://github.com/Phucdz2112/Web_QC_sanpham

Ứng dụng PHUC STUDIO giới thiệu thiết bị cho góc làm việc. Trang công khai có danh mục, chi tiết và giao diện responsive; WordPress quản trị thêm, sửa, xóa và xuất bản sản phẩm. Giá được chuẩn hóa thành số nguyên không âm. Hình SVG do dự án tạo là minh họa giao diện, không phải ảnh chụp sản phẩm thật. Không có thanh toán hoặc gửi thư thật.

## Kiến trúc

```text
Browser -> Nginx :8082 -> WordPress Apache -> MySQL
SSH tunnel -> phpMyAdmin :5432 / Grafana :3002 / Prometheus :9091
Prometheus -> cAdvisor / nginx-exporter / mysql-exporter
Grafana -> Prometheus + Loki
Nginx access log + WordPress audit log -> Promtail -> Loki
```

Tất cả dịch vụ chạy bằng Docker Compose. `docker-compose.yml` chứa web, DB, phpMyAdmin và Nginx; `compose.monitoring.yml` bổ sung monitoring; `compose.logging.yml` bổ sung logging. `scripts/dc.sh` ghép cả ba file. Không dùng Docker Desktop trên VM Ubuntu.

## Chạy trên Ubuntu mới

Yêu cầu Docker Engine và Compose plugin, Python 3, Git. Khuyến nghị RAM 4 GB. Máy lab 2 vCPU, RAM khả dụng khoảng 1,6 GiB cần swap; các dịch vụ có giới hạn bộ nhớ.

```bash
git clone https://github.com/Phucdz2112/Web_QC_sanpham
cd Web_QC_sanpham
python3 scripts/create-env.py
```

Sửa `BIND_IP` và `SITE_URL` trong `.env` theo IP máy. Mật khẩu được sinh ngẫu nhiên riêng cho từng tài khoản, không in ra terminal và không đưa vào Git. Cấp quyền Docker theo chính sách máy; nếu tài khoản chưa được cấp, chạy các lệnh Docker với sudo.

```bash
docker compose up -d --build --wait --wait-timeout 300
sh scripts/install.sh
python3 scripts/setup-exporter.py
sh scripts/dc.sh up -d
sh scripts/dc.sh ps
```

Không chạy `create-env.py` để thay mật khẩu database đã tồn tại. Với named volume cũ, thay `.env` không đổi tài khoản đã lưu trong MySQL; phải backup và cập nhật SQL tương ứng trước. Trên máy bàn giao, Compose project là `project`, giữ `project_wordpress_data` và `project_mysql84_data`. Đổi tên project tạo bộ volume khác, không tự chuyển dữ liệu.

## Truy cập và tài khoản

Website: http://192.168.74.141:8082 ; quản trị: `/wp-admin/`. Từ Windows mở terminal và giữ SSH tunnel:

```bash
ssh -N -L 5432:127.0.0.1:5432 -L 3002:127.0.0.1:3002 -L 9091:127.0.0.1:9091 -L 3101:127.0.0.1:3101 phuc2102@192.168.74.141
```

| Thành phần | Địa chỉ trên Windows | Tài khoản | Mật khẩu trong `.env` trên VM |
|---|---|---|---|
| WordPress | Website `/wp-admin/` | `DTC255180105` | `WP_ADMIN_PASSWORD` |
| phpMyAdmin | http://localhost:5432 | `wordpress` | `WORDPRESS_DB_PASSWORD` |
| Grafana | http://localhost:3002 | `DTC255180105` | `GRAFANA_ADMIN_PASSWORD` |
| Prometheus | http://localhost:9091 | Không bật auth trong lab | Qua SSH tunnel |
| Loki API | http://localhost:3101 | Không bật auth trong lab | Qua SSH tunnel |

Tài khoản root chỉ dùng bảo trì, không dùng làm tài khoản ứng dụng. `.env` mode 600. Không chụp, gửi lên Git hoặc ghi mật khẩu vào báo cáo. Địa chỉ email example.test chỉ phục vụ minh họa.

## Giám sát

Grafana tự provision hai datasource Prometheus và Loki, folder `DTC255180105`, dashboard UID `web-qc-system`. Dashboard gồm trạng thái Nginx/MySQL, scrape targets, số container, CPU, RAM, lưu lượng mạng, tốc độ request web và truy vấn DB.

Trong Prometheus kiểm tra:

```promql
up
nginx_up
mysql_up
count(container_last_seen{name!=""})
```

Phải có `nginx_up = 1`, `mysql_up = 1` và metrics container không rỗng. Target exporter `UP` chỉ chứng minh exporter phản hồi HTTP; không đảm bảo nó kết nối được web/DB. Tạo traffic rồi đợi hai chu kỳ scrape trước khi xem rate. CPU là phần trăm một lõi; tổng máy nhiều lõi có thể vượt 100%. Network rate có thể đếm trùng giữa interface, không coi tổng các container là lưu lượng host duy nhất.

## Log tập trung và LogQL

Promtail đọc shared volumes ở chế độ chỉ đọc, gắn nhãn job/project có cardinality thấp rồi gửi Loki. File positions nằm trên volume riêng. Nginx log JSON không ghi query string, cookie, token hoặc request body. WordPress audit chỉ ghi sự kiện và ID nội bộ.

Trong Grafana Explore chọn datasource Loki, thời gian 15 phút gần nhất:

```logql
{project="web-qc-sanpham",job="nginx"} | json
```

```logql
{project="web-qc-sanpham",job="nginx"} | json | status >= 400
```

```logql
{project="web-qc-sanpham",job="wordpress"} | json | event=~"login_success|login_failed|product_saved|product_deleted"
```

Truy cập website, mở đường dẫn không tồn tại, đăng nhập và thêm/sửa/xóa sản phẩm thử để tạo dữ liệu thật. Chụp kết quả có dòng log, không chỉ chụp câu query. Promtail đã EOL ngày 02/03/2026; giữ trong lab theo yêu cầu đề, production cần chuyển sang Alloy: https://grafana.com/docs/loki/latest/send-data/promtail/

## Hardening

* Nginx UID 101; Prometheus/exporters UID 65534; Grafana UID 472; Loki UID 10001. Nginx và một số dịch vụ có filesystem chỉ đọc, `cap_drop: ALL`, `no-new-privileges`.
* Tách mạng frontend, backend internal, admin và monitoring. MySQL, exporters và cAdvisor không publish cổng. Công cụ quản trị chỉ bind loopback.
* Mật khẩu ngẫu nhiên riêng biệt; không dùng root cho ứng dụng. User `wordpress` chỉ có quyền schema `wordpress`; user exporter riêng theo quyền đọc cần thiết của mysqld_exporter.
* Nginx thêm X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy; ẩn version, chặn dotfiles/XML-RPC và hạn chế tốc độ đăng nhập. WordPress dùng phân quyền, nonce và escaping; tắt sửa file qua admin.
* Log Docker giới hạn 5 MB × 3 file; volumes giữ dữ liệu qua recreate. Backup nằm ngoài Git, file mode 600.

Ngoại lệ phải hiểu khi demo: init-logs cần root chown; Apache master của WordPress/phpMyAdmin khởi động root rồi chạy worker www-data; MySQL entrypoint hạ quyền sang mysql; Promtail root đọc log volumes nhưng drop capabilities; cAdvisor privileged để đọc metrics host. Không tuyên bố tất cả container đều non-root. `.env` vẫn là bí mật dạng file, người có quyền Docker có thể đọc nó.

HTTP kèm security headers đáp ứng lựa chọn trong đề; chưa có TLS nên chỉ dùng trong mạng VM tin cậy. Không bật HSTS khi chưa có HTTPS. Không công khai các cổng quản trị ra Internet.

## Backup và kiểm thử

```bash
python3 scripts/backup.py /home/phuc2102/web-qc-artifacts/backups
EVIDENCE_DIR=/home/phuc2102/web-qc-artifacts/evidence python3 tests/check.py
```

`tests/check.py` là kiểm tra tích hợp read-only, ghi JSON ngoài repository. Kiểm thử trình duyệt trong `tests/browser.py` cần Python Playwright và Chromium; script tạo rồi xóa sản phẩm thử trên lab, đăng nhập các công cụ và chụp màn hình thật. Không chạy thử CRUD trên production nếu chưa có backup.

Không chạy `docker compose down -v`, `volume prune` hay import SQL đè lên database thật. Thử phục hồi bằng DB mới hoặc một Compose project độc lập, xác nhận số bản ghi và chức năng trước khi chuyển đổi. Backup SQL không thay thế backup wp-content/uploads.

## Mốc commit và minh chứng

1. Ứng dụng WordPress, MySQL, phpMyAdmin, Nginx và hardening nền tảng.
2. Prometheus, cAdvisor, exporters và dashboard Grafana được provision.
3. Loki, Promtail, ba LogQL và kiểm tra tích hợp.

GitHub chỉ chứa code, SVG giao diện, cấu hình, scripts, tests và README. Báo cáo Word/PDF, screenshots, dump database, dữ liệu runtime và credentials được lưu bên ngoài repository theo yêu cầu bàn giao. Tài khoản GitHub hiện là Phucdz2112; mã SV thể hiện trong tác giả, tài khoản ứng dụng và dashboard. Nếu giảng viên yêu cầu chính tên đăng nhập GitHub trùng mã SV, cần xử lý riêng trên tài khoản GitHub.

## Kịch bản demo

Mở website và một trang chi tiết; đăng nhập WordPress bằng mã SV và thao tác sản phẩm; mở phpMyAdmin kiểm tra bảng; mở Prometheus Targets và hai metric availability; mở dashboard Grafana; chạy ba LogQL với log mới; trình bày networks, cổng, UID, headers, quyền DB và cách bảo vệ secrets; cuối cùng mở GitHub để đối chiếu commits và README.
