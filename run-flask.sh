export FLASK_APP=./main.py

if [ ! -d venv ]
then
  virtualenv -p /usr/bin/python3 venv
fi

source venv/bin/activate
pip3 install flask
pip3 install netaddr

while [ 1 == 1 ]
do
  echo `date` >> start.log
  flask run # --host=0.0.0.0
  sleep 5
done
