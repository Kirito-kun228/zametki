данный репозиторий посвящен созданию веб сервиса в рамках тестового задания. 
В веб сервисе выполнены все условия тз, есть файл тестовых запросов, код отформатирован с помощью yapf. 

Сам сервис работает на фреймворке fastAPI, является полностью асинхронным, имеет несколько функций для обработки post/get/delete запросов, возможность аутентификации пользователей, возможность создавать заметки.

 ссылка на докер-контейнер https://hub.docker.com/repository/docker/kiritokun1337/testovoe_zadanie/general
 для запуска используйте команды `docker pull kiritokun1337/testovoe_zadanie:latest`
 а после `docker run -d -p 8000:8000 dockerhub_kiritokun1337/testovoe_zadanie:latest`
