expt: actual.txt

actual.txt:
	echo \# actual result on `date` > actual.txt
	python expt.py >> actual.txt

check: actual.txt
	diff -y actual.txt expected.txt || true

unittest:
	python testexpt.py 

clean:
	rm -f *~ *.pyc actual.txt

