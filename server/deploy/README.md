# Деплой сервера TechPrice на Azure (для проверки)

Сервер запускается на виртуальной машине Azure только тогда, когда нужен.
Пока машина остановлена (Stopped (deallocated)), бесплатные часы не тратятся.

## 1. Создать виртуальную машину (один раз)

1. Активировать Azure for Students со страницы предложений GitHub Student Developer Pack.
2. portal.azure.com → Virtual machines → Create → Azure virtual machine:
   - Resource group: новая, `techprice`
   - Virtual machine name: `techprice`
   - Region: ближайший к Молдове, где доступен B1s (Poland Central, Germany West Central, North Europe)
   - Image: **Ubuntu Server 24.04 LTS**
   - Size: **Standard_B1s** (с пометкой free services eligible)
   - Authentication type: SSH public key, Username: `azureuser`, Key pair: Generate new
   - Public inbound ports: SSH (22)
   - Вкладка Management → **Auto-shutdown: On**, например 23:00, часовой пояс Кишинёва.
     Машина выключится сама, если забыть её остановить.
3. Create → Download private key → файл `techprice_key.pem` сохранить в `C:\Users\migov\.ssh\`.
4. Машина → Networking (Network settings) → Create port rule → Inbound:
   Destination port ranges `8080`, Protocol TCP, Name `techprice-api` → Add.
5. Машина → Overview → Public IP address → открыть настройки IP:
   Assignment должен быть **Static**, иначе после остановки адрес сменится.
   Там же можно задать DNS name label, например `techprice-migov`, тогда адрес будет
   `techprice-migov.<регион>.cloudapp.azure.com`.

## 2. Установить сервер (один раз)

В PowerShell:

```powershell
ssh -i $HOME\.ssh\techprice_key.pem azureuser@<IP>
```

Если ssh ругается на права ключа (UNPROTECTED PRIVATE KEY FILE):

```powershell
icacls $HOME\.ssh\techprice_key.pem /inheritance:r
icacls $HOME\.ssh\techprice_key.pem /grant:r "$($env:USERNAME):(R)"
```

На машине:

```bash
git clone https://github.com/Voland13915/PAM.git
cd PAM/server
bash deploy/setup.sh
```

Если репозиторий приватный, git спросит логин и пароль: вместо пароля нужен
Personal access token (GitHub → Settings → Developer settings → Personal access tokens).

Скрипт ставит Python-окружение и зависимости, добавляет 1 ГБ подкачки,
создаёт секрет для токенов в `/etc/techprice.env` и службу `techprice`,
которая запускает сервер при каждом включении машины.
В конце он печатает адрес вида `http://<IP>:8080/health`. Открой его в браузере
на телефоне: должен прийти ответ сервера.

## 3. Проверить, что магазины отдают страницы облаку

Магазины могут блокировать адреса дата-центров, поэтому это стоит проверить сразу:

```bash
cd ~/PAM/server
.venv/bin/python -m app.scrape all --max-pages 1 --dry-run
```

По каждому магазину должны появиться найденные товары. Если какой-то магазин
отвечает 403 или таймаутом, значит он блокирует облако: сервер всё равно работает,
просто цены этого магазина будут только из перенесённой базы.

## 4. Перенести свою базу (чтобы не собирать цены заново)

1. Остановить локальный сервер (Ctrl+C), чтобы база полностью записалась на диск.
2. На машине: `sudo systemctl stop techprice`
3. В PowerShell из папки `PAM`:

   ```powershell
   scp -i $HOME\.ssh\techprice_key.pem server\app.db azureuser@<IP>:~/PAM/server/app.db
   ```

4. На машине: `sudo systemctl start techprice`

Аккаунты пользователей переносятся вместе с базой.
Без переноса база будет пустой, и через минуту после запуска начнётся полный сбор цен.
На B1s он займёт заметно больше времени, чем на компьютере.

## 5. Собрать приложение под сервер

```powershell
flutter build apk --release --dart-define=API_BASE=http://<IP или DNS-имя>:8080
adb install -r build\app\outputs\flutter-apk\app-release.apk
```

APK можно и просто отправить на любой телефон: компьютер и `adb reverse` больше не нужны.
Соединение идёт по HTTP без шифрования, поэтому для проверки лучше завести
отдельный аккаунт, а не использовать свой обычный пароль.

## Каждый раз при проверке

| Действие | Где |
|---|---|
| Включить | Portal → машина `techprice` → **Start**. Сервер стартует сам примерно через минуту |
| Свежие цены | Если последний сбор был больше 20 часов назад, он начнётся сам через минуту после запуска. Ход сбора: Профиль → Отслеживаемые магазины |
| Выключить | Portal → **Stop**, статус должен стать **Stopped (deallocated)** |

## Обновить сервер после новых коммитов

```bash
cd ~/PAM/server
bash deploy/update.sh
```

## Если что-то не так

| Симптом | Что проверить |
|---|---|
| Не открывается `http://<IP>:8080/health` | Правило для порта 8080 в Networking; `systemctl status techprice` |
| Ошибка при запуске | `journalctl -u techprice -n 100 --no-pager` |
| Приложение не подключается | Адрес в `--dart-define=API_BASE`, машина включена, IP не сменился |
| Сбор цен не идёт | `ls ~/PAM/server/logs` и последний файл `scrape-*.log` |
