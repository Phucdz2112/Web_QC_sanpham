# Demo trên máy ảo Ubuntu

Làm việc tại `/home/phuc2102/Project`, tài khoản `phuc2102`. Các lệnh dưới đây là **Bash trong Ubuntu**, dùng sudo khi tài khoản chưa có quyền Docker. Máy thật Windows chỉ mở trình duyệt hoặc SSH tunnel.

## Khởi động và kiểm tra

```bash
cd ~/Project
sudo docker compose config --quiet
sudo docker compose up -d --build
sudo docker compose ps -a
```

Chỉ có một `docker-compose.yml`. `init-logs`, `database-init`, `wordpress-init` là tác vụ khởi tạo, kết thúc với mã 0; 11 dịch vụ dài hạn tiếp tục chạy. Database, WordPress, Nginx và cAdvisor có healthcheck. Không dùng profiles, override hoặc wrapper ghép nhiều file.

Các mật khẩu được đọc từ `.env`, không in file này lên màn hình khi demo. `.env.example` chỉ chứa giá trị mẫu. Với clone mới, chạy `python3 scripts/create-env.py` và sửa IP/cổng cần thiết trước lệnh khởi động. Với máy bàn giao có dữ liệu, giữ `.env` hiện tại.

## Thao tác cấu hình nhanh

| Giảng viên yêu cầu | File hoặc biến cần sửa | Lệnh áp dụng tối thiểu trên Ubuntu | Cách xác nhận |
|---|---|---|---|
| Đổi cổng web | `WEB_PORT` trong `.env` | `sudo docker compose config --quiet` rồi `sudo docker compose up -d --no-deps wordpress nginx` | Mở `http://192.168.74.141:CỔNG_MỚI`, kiểm tra URL ảnh và trang chi tiết. WordPress và CLI tự nhận URL từ IP/cổng. |
| Đổi cổng Grafana | `GRAFANA_PORT` | `sudo docker compose up -d --no-deps grafana` | Tạo SSH tunnel tới cổng mới, mở `/api/health` và dashboard. |
| Đổi cổng phpMyAdmin | `PHPMYADMIN_PORT` | `sudo docker compose up -d --no-deps phpmyadmin` | Cập nhật tunnel rồi đăng nhập bằng user DB ứng dụng. Không mở DB 3306. |
| Đổi cổng Prometheus hoặc Loki | `PROMETHEUS_PORT`, `LOKI_PORT` | `sudo docker compose up -d --no-deps prometheus loki` | Cập nhật tunnel, kiểm tra Targets hoặc `/ready`. URL datasource nội bộ không đổi. |
| Sửa nội dung sản phẩm | WordPress `/wp-admin/`, mục Sản phẩm | Lưu hoặc cập nhật sản phẩm trong admin | Tải lại trang chi tiết; kiểm tra giá, nội dung và audit log. |
| Sửa CSS hoặc theme đang mount | `app/theme/` | Không cần build để xem bind mount; tải lại trình duyệt | Kiểm tra font và giao diện; CSS có version theo thời gian sửa file. Build lại image khi chuẩn bị bàn giao source mới. |
| Sửa Dockerfile hoặc source được COPY | `Dockerfile`, `app/` | `sudo docker compose up -d --build wordpress wordpress-init` | Xem log build, health và chức năng. Bind mount hiện tại có ưu tiên so với nội dung image. |
| Sửa Nginx | `nginx/nginx.conf` | `sudo docker compose exec nginx nginx -t` rồi `sudo docker compose exec nginx nginx -s reload` | `curl -I http://192.168.74.141:8082/`, kiểm tra status và headers. |
| Đổi chu kỳ scrape | `scrape_interval` trong `monitoring/prometheus.yml` | `sudo docker compose exec prometheus promtool check config /etc/prometheus/prometheus.yml` rồi `sudo docker compose kill -s HUP prometheus` | Targets và API `/api/v1/status/config` thể hiện cấu hình mới; chờ ít nhất hai chu kỳ trước khi xem rate. |
| Sửa LogQL | `logging/queries.logql` để lưu; ô query trong Grafana Explore để chạy | Không recreate container chỉ vì đổi query | Chọn Loki, time range phù hợp và xác nhận có dòng log. |
| Xem lỗi một dịch vụ | Ví dụ `nginx`, `mysql`, `promtail` | `sudo docker compose logs --tail 80 nginx` | Đọc lỗi cụ thể trước khi sửa; không in toàn bộ cấu hình có secrets. |
| Khởi động lại tiến trình | Tên service thực tế | `sudo docker compose restart nginx` | Kiểm tra health và HTTP; restart không áp dụng port mapping hoặc environment mới. |

Trong bảng, `CỔNG_MỚI` là giá trị vừa đặt vào `.env`; bài thực hành dưới đây dùng chính cổng 8083 sau khi kiểm tra còn trống, không chạy nguyên một placeholder trong terminal.

## Bài thực hành đổi cổng web rồi trả về

Trước tiên sao lưu, kiểm tra cổng 8083 chưa được dịch vụ nào dùng:

```bash
sudo python3 scripts/backup.py /home/phuc2102/web-qc-artifacts/backups/port-demo
ss -lnt
```

Nếu cổng 8083 còn trống, sửa và áp dụng:

```bash
sed -i 's/^WEB_PORT=8082$/WEB_PORT=8083/' .env
sudo docker compose config --quiet
sudo docker compose up -d --no-deps wordpress nginx
curl -I http://192.168.74.141:8083/
```

Mở trang chủ, một sản phẩm và ảnh ở cổng 8083. Sau đó đưa về:

```bash
sed -i 's/^WEB_PORT=8083$/WEB_PORT=8082/' .env
sudo docker compose up -d --no-deps wordpress nginx
curl -I http://192.168.74.141:8082/
```

Kiểm tra lại danh sách sản phẩm và dữ liệu DB. Giữ nguyên `name: project`, `wordpress_data`, `mysql84_data`; không xóa volume. Chỉ dùng ví dụ 8083 khi cổng đã được kiểm tra trống.

## Truy cập từ Windows

**PowerShell trên Windows**, giữ cửa sổ SSH này đang chạy:

```powershell
ssh -N -L 5432:127.0.0.1:5432 -L 3002:127.0.0.1:3002 -L 9091:127.0.0.1:9091 -L 3101:127.0.0.1:3101 phuc2102@192.168.74.141
```

Website dùng IP VM và cổng web. phpMyAdmin mở `http://localhost:5432`, Grafana `http://localhost:3002`, Prometheus `http://localhost:9091`. User web/Grafana mặc định `DTC255180105`; phpMyAdmin dùng `wordpress`. Mật khẩu riêng trong `.env` trên VM. Khi đổi cổng quản trị, sửa đích tunnel tương ứng; không thay localhost của VM bằng localhost Windows một cách tùy ý.

## Metrics, log và hardening

Trong Prometheus kiểm tra `up`, `nginx_up`, `mysql_up` và `count(container_last_seen{name!=""})`. Các giá trị dịch vụ phải bằng 1; exporter UP chưa đủ chứng minh kết nối DB/web thành công. Grafana có dashboard UID `web-qc-system`.

Trong Explore chọn datasource Loki, chạy ba query trong `logging/queries.logql`. Truy cập web, URL không tồn tại hoặc thao tác một sản phẩm thử để tạo log mới.

Kiểm tra bảo mật mà không in secrets:

```bash
sudo docker compose exec nginx id
sudo docker network inspect project_backend --format '{{.Internal}}'
sudo docker compose ps
curl -I http://192.168.74.141:8082/
sudo ufw status verbose
```

Nginx UID 101; backend internal; DB không publish; admin loopback; headers hiện trong phản hồi. UFW có thể inactive trong lab; ghi đúng kết quả, không tuyên bố firewall đã bật. Docker publish có cơ chế firewall riêng, vì vậy ưu tiên bind loopback và không publish DB. Không bật firewall hoặc sửa SSH tùy tiện trong lúc đang SSH.

Đổi `MYSQL_DATABASE`, `MYSQL_USER` hoặc mật khẩu trên volume cũ cần backup và thao tác SQL/cập nhật kết nối tương ứng; sửa `.env` không tự đổi dữ liệu hay tài khoản đã lưu. Không dùng root để đăng nhập web.

## Dừng mà giữ dữ liệu

```bash
sudo docker compose stop
```

Khởi động lại bằng `sudo docker compose up -d`. Không dùng `down -v`, `volume prune` hoặc reset database để demo nhanh.
