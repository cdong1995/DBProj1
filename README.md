## Project Part 1.3

### SQL Account
postgresql://cd3032:2203@34.73.21.127/proj1part2


### URL To Our Web Server
http://34.73.15.31:8111/

### How to login to our server
Use the following user-name and password to login to the system.

#### 1. Users
- username: Sam, password: 123456
- username: Amy, password: 123456

#### 2. Administrators
- username: admin_1, password: 123456
- username: Hank, password: fuckingpassword

### Description-SQL

#### 1. Changes to part 1
We found that in our project part 1, we forgot to account for the 'likes' attribute for
the content table. Imagining adding a button to the web page where user can click to 'like' a
post. Without creating another relationship monitoring whether a user has already 'liked' a post,
the 'likes' of the post can grow arbitrarily. So we created a new table 'like_relation' to monitor it.

#### 2. A wide variety of SQL commands
We used a number of SQL commands in our code, here is a list:
- common operations: **INSERT, DELETE, SELECT**
- groups: **GROUP BY, ORDER BY ASC, ORDER BY DESC**
- joins: **LEFT JOIN, RIGHT JOIN**
- subqueries
- conditions: **AND, EXISTS**

#### 3. Interesting SQL commands

##### a. Robustness of 'INSERT' operations
When you logged in as one of the administrators, you can choose to publish an event
and the server will require you to fill out a form which has several fields such as location,
start date, end date etc.

At the backend, we need to perform INSERT on 
4 tables ('event', 'publish_relation', 'at_relation', 'address') and 1 SELECT (to check whether
the address is already in the database). The code written takes consideration of nearly all possible
exceptions that may occur and perform DELETE if necessary.

##### b. Implementing 'likes'
The major difficulty in this is to realize that not all posts (entries in the content table) has likes.
So a LEFT JOIN or RIGHT JOIN is required to get the correct counts.


### Description-HTML User Interface

### For users

#### 1. Login
Login using username and password.

#### 2. Profile
Modify interest-area and post a new image & text.

#### 3. World
View all posts.

#### 4. Follow
View all users that are followed by the current user.

### For adnimistrators

#### 1. Events
View all events **published by the administrator**. The administrator can't view or delete
events by other administrators.

#### 2. Publish Events
Publish a new event, potentially create new addresses.

