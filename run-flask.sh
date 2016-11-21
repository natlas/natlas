export FLASK_APP=main.py

while [ 1 == 1 ]
do
  echo `date` >> start.log
  python3 -m flask run # --host=0.0.0.0
  sleep 5
done
