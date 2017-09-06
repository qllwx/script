sudo apt install git
sudo apt install ruby ruby-dev ruby-bundler
gem sources --add https://gems.ruby-china.org/ --remove https://rubygems.org/
#bundle config mirror.https://rubygems.org https://gems.ruby-china.org
sudo apt install gmp-doc libgmp10-doc libmpfr-dev

sudo apt-get install zlib1g-dev
sudo apt-get install libxslt1-dev libxml2-dev
sudo gem install rails
sudo apt-get install libsqlite3-dev
sudo gem install sqlite3

sudo apt-get install nodejs
ruby -v
rails -v
bundler -v
sqlite3 --version
rails new blog
cd blog
rails s


