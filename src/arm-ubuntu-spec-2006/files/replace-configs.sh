# fixes the first error in Zhantong's errors file

for dir in /home/gem5/spec2006/tools/src/expat-1.95.8/conftools /home/gem5/spec2006/tools/src/tar-1.15.1/config /home/gem5/spec2006/tools/src/specinvoke /home/gem5/spec2006/tools/src/make-3.80/config; do

cd $dir
echo "12345" | sudo rm config.guess config.sub
wget -O config.guess 'https://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.guess;hb=HEAD'
wget -O config.sub 'https://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.sub;hb=HEAD'

done