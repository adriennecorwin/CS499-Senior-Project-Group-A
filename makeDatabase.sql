/*
Mysql-connector-python
/usr/local/mysql/bin/mysql -uroot -p
*/
use SupremeCourtTwitter

DROP TABLE IF EXISTS url_log;
DROP TABLE IF EXISTS hashtag_log;
DROP TABLE IF EXISTS tweet;
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS hashtag;
DROP TABLE IF EXISTS url;

CREATE TABLE user (
  username VARCHAR(50),
  screen_name VARCHAR(50),
  location VARCHAR(100),
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

CREATE TABLE tweet (
  tweet_id INT(6) AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50),
  created_at DATETIME,
  is_retweet BOOLEAN,
  original_text VARCHAR(500),
  comment_text VARCHAR(500),
  num_retweets_original INT(6),
  num_retweets_new INT(6),
  num_favorites_original INT(6),
  num_favorites_new INT(6),
 /* last_updated DATETIME,*/
  FOREIGN KEY (username) REFERENCES user(username)
  ON DELETE CASCADE
  ON UPDATE CASCADE
);

CREATE TABLE hashtag_log (
  tweet_id INT(6),
  hashtag_text VARCHAR(100),
  FOREIGN KEY (tweet_id) REFERENCES tweet(tweet_id)
  ON DELETE CASCADE
  ON UPDATE CASCADE,
  FOREIGN KEY (hashtag_text) REFERENCES hashtag(hashtag_text)
  ON DELETE CASCADE
  ON UPDATE CASCADE
);

CREATE TABLE url_log (
  tweet_id INT(6),
  url_text VARCHAR(100),
  FOREIGN KEY (tweet_id) REFERENCES tweet(tweet_id)
  ON DELETE CASCADE
  ON UPDATE CASCADE,
  FOREIGN KEY (url_text) REFERENCES url(url_text)
  ON DELETE CASCADE
  ON UPDATE CASCADE
);

