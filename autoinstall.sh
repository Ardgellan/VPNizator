Red=$'\e[1;31m'
Green=$'\e[1;32m'
Blue=$'\e[1;34m'
Defaul_color=$'\e[0m'
Orange=$'\e[1;33m'
White=$'\e[1;37m'

#some builds minimize system, unminimize it to get all default utilities
yes | unminimize

sudo apt install -y curl
#clear screen after install curl
clear

#get server external ip
server_ip=$(curl -s ifconfig.me)

if [ -z "$server_ip" ]
then
      echo "$Red Can't get server external ip" | sed 's/\$//g'
      echo "$Red Check your internet connection" | sed 's/\$//g'
      echo "$Red Fail on command: curl -s ifconfig.me" | sed 's/\$//g'
      exit 1
fi

clear
echo $Blue | sed 's/\$//g'
echo "This script will install VPNizator telegram bot on your server"
echo "It will install and configure:"
echo $Orange | sed 's/\$//g'
echo "- XRAY (XTLS-Reality)"
echo "- PostgreSQL"
echo "- Python 3.11"
echo "- Poetry"
echo "- Telegram Bot for manage XRAY"
echo $Red | sed 's/\$//g'
echo "............................................................"
echo "...................//////////////..........................."
echo "............................................................"

echo $White | sed 's/\$//g'

echo "Now need to input some data for bot configuration"
echo "You can change it later in ~/VPNizator/data/.env file"
echo ""


#ask for bot token
echo "Enter bot token:"
echo "You can get it from $Blue @BotFather"
read bot_token

# ask user for Yookassa Shop ID
echo ""
echo "Enter Yookassa Shop ID:"
echo "Just press ENTER for use default test shop ID [$Blue 000000 $White]" | sed 's/\$//g'
read yookassa_shop_id
if [ -z "$yookassa_shop_id" ]
then
      yookassa_shop_id="000000"  # Укажи здесь тестовый shop_id, если нужно
fi

# ask user for Yookassa API token
echo ""
echo "Enter Yookassa API token (for test or real payments):"
echo "Just press ENTER for use default test token [$Blue test_api_token_example $White]" | sed 's/\$//g'
read yookassa_api_token
if [ -z "$yookassa_api_token" ]
then
      yookassa_api_token="test_api_token_example"
fi

#ask user for admins ids
echo ""
echo "Enter admins ids (separated by comma):"
echo "Just press ENTER for use default ids [$Blue 123456789, $White]" | sed 's/\$//g'
echo "You can get your id by sending /id command to @userinfobot"
read admins_ids
if [ -z "$admins_ids" ]
then
      admins_ids="123456789,"
fi

#ask user for admins ids
echo ""
echo "Enter admins ids (separated by comma):"
echo "Just press ENTER for use default ids [$Blue nginxtest.vpnizator.online, $White]" | sed 's/\$//g'
echo "You can get your id by sending /id command to @userinfobot"
read proxy_server_domain
if [ -z "$proxy_server_domain" ]
then
      proxy_server_domain="nginxtest.vpnizator.online"
fi

#ask user for Database name
echo ""
echo "Enter Database name:"
echo "Just press ENTER for use default name [$Blue vpnizator_database $White]" | sed 's/\$//g'
read database_name
if [ -z "$database_name" ]
then
      database_name="vpnizator_database"
fi

#ask user for Database user
echo ""
echo "Enter Database user:"
echo "Just press ENTER for use default user [$Blue vpnizator_database_user $White]" | sed 's/\$//g'
read database_user
if [ -z "$database_user" ]
then
      database_user="vpnizator_database_user"
fi

#ask user for Database password
echo ""
echo "Enter Database user password:"
echo "Just press ENTER for use default password [$Blue starscream $White]" | sed 's/\$//g'
read database_passwd
if [ -z "$database_passwd" ]
then
      database_passwd="starscream"
fi

#all neccessary data is collected
echo ""
echo "All neccessary data is collected"
echo "Now script will install all needed software (it can take some time)"
echo "$White" | sed 's/\$//g'
echo "Wanna update system before install? [y/N]"
echo "$Defaul_color" | sed 's/\$//g'
read update_system
if [ "$update_system" = "y" ]
then
      sudo apt update && sudo apt upgrade -y
fi

#install packages
sudo apt install -y git bat tmux mosh postgresql postgresql-contrib
systemctl start postgresql.service

#install python3.11 and pip
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-dev python3.11-distutils python3.11-venv
sudo curl https://bootstrap.pypa.io/get-pip.py -o /root/get-pip.py
python3.11 /root/get-pip.py

#install poetry
pip3.11 install poetry

#configure postgresql
su - postgres -c "psql -c \"CREATE USER $database_user WITH PASSWORD '$database_passwd';\""
su - postgres -c "psql -c \"CREATE DATABASE $database_name;\""
su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON SCHEMA public TO $database_user;\""
su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE $database_name TO $database_user;\""

# Установка часового пояса на Москву
echo "Настраиваем часовой пояс на Москву..."
sudo timedatectl set-timezone Europe/Moscow

#clone bot repo
cd ~
git clone https://github.com/Ardgellan/VPNizator.git

#create venv and install bot dependencies
cd ~/VPNizator
git switch develop
poetry install --no-root
cd

#configure bot .env file
sudo cat <<EOF > ~/VPNizator/source/data/.env
TG_BOT_TOKEN = "$bot_token"
YOOKASSA_SHOP_ID = "$yookassa_shop_id"
YOOKASSA_API_TOKEN = "$yookassa_api_token"
ADMINS_IDS = "$admins_ids"
PROXY_SERVER_DOMAIN = "$proxy_server_domain"

DB_NAME = "$database_name"
DB_USER = "$database_user"
DB_USER_PASSWORD = "$database_passwd"
DB_HOST = "localhost"
DB_PORT = "5432"

XRAY_CONFIG_PATH = "/usr/local/etc/xray/config.json"
EOF

#try to run create_database_tables.py if it fails, then give db user superuser privileges
cd ~/VPNizator
$(poetry env info --path)/bin/python3.11 create_database_tables.py || -u postgres psql -c "ALTER USER $database_user WITH SUPERUSER;" && $(poetry env info --path)/bin/python3.11 create_database_tables.py
cd

#create systemd service for bot
cd ~/VPNizator
sudo cat <<EOF > /etc/systemd/system/vpnizator.service
[Unit]
Description=VPNizator telegram bot
After=network.target

[Service]
Type=simple
User=$current_os_user
ExecStart=/bin/bash -c 'cd ~/VPNizator/ && $(poetry env info --executable) app.py'
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
cd

#enable and start bot service
systemctl daemon-reload
systemctl enable vpnizator.service
# systemctl start vpnizator.service

echo "$Green Installation completed successfully" | sed 's/\$//g'
echo "$Defaul_color" | sed 's/\$//g'

echo "$Blue Your .env file losudo cated at $Orange ~/VPNizator/source/data/.env" | sed 's/\$//g'
echo "$Blue Do u want to watch it? [ y / $Blue N $White]" | sed 's/\$//g'
read watch_env_file

if [ "$watch_env_file" = "y" ]
then
      sudo batcat ~/VPNizator/source/data/.env
fi

echo "$Blue Your bot logs losudo cated at $Orange ~/VPNizator/logs/" | sed 's/\$//g'
#thanks for install
echo "$Green Thanks for install" | sed 's/\$//g'
echo "$Defaul_color" | sed 's/\$//g'
