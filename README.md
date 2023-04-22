<h1>Всем доброго времени суток</h1>
<h3>В 1 блоке будет про логику самого проекта (пока конкретно глобуса), ниже, во 2 блоке, сможете ознакомиться с подробной инструкцией</h3>
<h2>Логика</h2>
<h4>1. Работу парсера можно поделить на 2 компонента: часть с джангой и часть с хэд менеджмент файлом</h4>
<h4>2. Хэд менеджмент файл отправляет запрос к джанге на сбор категорий в отдельный файл categories.txt. После получения ответа, хэд-файл итерирует файл с категориями и по каждой отправляет запрос в сторону джанги</h4>
<h4>3. Со стороны джанги происходит асинхронный парсинг каждой категории: каждая категория разбивается на список из тасок парсинга определенной страницы категории, и каждая таска в свою очередь включает в себя список тасок из парсинга товаров на той самой пронумерованной странице.</h4>
<h4>4. После того, как все таски на определнную категорию отработали, выполняется проверка на то, что вернули таски. Если какая-то из тасок вернула не список, то джанга возвращает 400. Если все прошло  хорошо и все таски вернули по списку, то для каждого списка формируется json файл и пачка объектов класса Product раздергивается на словари. Джанга возвращает 200</h4>
<h4>5. Если хфэд файлик получил по каждой категории 200, то начинается повторная итерация файлика с категориями, но на этот раз на открытие json файлика с товарами по каждой категории. Содержимое каждого файла добавляется в мейн список словарей. Файл удаляется сразу после использования, мейн список дампиться в файлик globus.json</h4>
<h2>Инструкция</h2>
<h5>[ ! ] Дисклейрмер [ ! ] Возможно в некоторых командах нужно будет заменить pip и python на pip3 и python3 соответственно</h5>
<h4>1. В той же директории, в которую был скачан проект, введите следующую команду:</h4>
<strong>pip install -r requirements.txt</strong>
<h4>2. После успешной установки всех требуемых библиотек, перейдите в директорию ниже уровнем (команда для винды):</h4>
<strong>cd dynamic_panel</strong>
<h4>3. В директории dynamic_panel (та, в которой находятся файлик manage.py) запускаете следующую команду:</h4>
<strong>python manage.py runserver</strong>
<h4>4. Если запускаете проект из консоли, то переходим в родительскую папку (ту, из которой запускали установку пакетов в 1 пункте) и пишем:</h4>
<strong>python head.py</strong>
<h4>Если нет, то просто запускаем файлик head.py с кнопки. Чтобы инциализировать время 1 парса, замените значение 2 агрумента класса Schedulerio на другое время в формате "%Y-%m-%d %H:%M"</h4>
<h2>Навигация</h2>
<h4>head.py - файлик управления процессами</h4>
<h4>head_services.py - вся логика файлика head.py вынесена сюда, чтобы не засерать файлик с точкой входа</h4>
<h4>globus/views.py - вьюхи, которые отзываются на линки. Файлик практически девсвенный, вся логика вынесена в отдельный файл</h4>
<h4>globus/services.py - файл с логикой к вьюхам</h4>