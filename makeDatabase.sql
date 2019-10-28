/*
Mysql-connector-python
/usr/local/mysql/bin/mysql -uroot -p
*/
use SupremeCourtTwitter

DROP TABLE IF EXISTS url_log;
DROP TABLE IF EXISTS hashtag_log;
DROP TABLE IF EXISTS tweets;
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS hashtag;
DROP TABLE IF EXISTS url;

CREATE TABLE user (
  username VARCHAR(50),
  screen_name VARCHAR(50),
  location VARCHAR(50),
  is_verified BOOLEAN,
  PRIMARY KEY (username)
);

CREATE TABLE hashtag (
  hashtag_text VARCHAR(100),
  PRIMARY KEY (hashtag_text)
);

CREATE TABLE url (
  url_text VARCHAR(100),
  PRIMARY KEY (url_text)
); 

CREATE TABLE tweets (
  tweet_id INT(6) AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50),
  created_at DATETIME,
  text VARCHAR(500),
  num_retweets INT(6),
  num_favorites INT(6),
 /* last_updated DATETIME,*/
  is_quote_tweet BOOLEAN,
  FOREIGN KEY (username) REFERENCES user(username)
  ON DELETE CASCADE
  ON UPDATE CASCADE
);

CREATE TABLE hashtag_log (
  tweet_id INT(6),
  hashtag_text VARCHAR(100),
  FOREIGN KEY (tweet_id) REFERENCES tweets(tweet_id)
  ON DELETE CASCADE
  ON UPDATE CASCADE,
  FOREIGN KEY (hashtag_text) REFERENCES hashtag(hashtag_text)
  ON DELETE CASCADE
  ON UPDATE CASCADE
);

CREATE TABLE url_log (
  tweet_id INT(6),
  url_text VARCHAR(100),
  FOREIGN KEY (tweet_id) REFERENCES tweets(tweet_id)
  ON DELETE CASCADE
  ON UPDATE CASCADE,
  FOREIGN KEY (url_text) REFERENCES url(url_text)
  ON DELETE CASCADE
  ON UPDATE CASCADE
);

