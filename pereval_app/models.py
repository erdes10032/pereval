from django.db import models


class User(models.Model):
    """Модель пользователя"""
    email = models.EmailField(unique=True)
    fam = models.CharField(max_length=255, verbose_name="Фамилия")
    name = models.CharField(max_length=255, verbose_name="Имя")
    otc = models.CharField(max_length=255, verbose_name="Отчество", blank=True)
    phone = models.CharField(max_length=20, verbose_name="Телефон")

    class Meta:
        db_table = 'pereval_user'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.fam} {self.name} ({self.email})"


class Coords(models.Model):
    """Модель координат"""
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Широта")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Долгота")
    height = models.IntegerField(verbose_name="Высота")

    class Meta:
        db_table = 'pereval_coords'
        verbose_name = 'Координаты'
        verbose_name_plural = 'Координаты'

    def __str__(self):
        return f"({self.latitude}, {self.longitude}, {self.height})"


class Level(models.Model):
    """Модель уровня сложности"""
    winter = models.CharField(max_length=10, verbose_name="Зима", blank=True)
    summer = models.CharField(max_length=10, verbose_name="Лето", blank=True)
    autumn = models.CharField(max_length=10, verbose_name="Осень", blank=True)
    spring = models.CharField(max_length=10, verbose_name="Весна", blank=True)

    class Meta:
        db_table = 'pereval_level'
        verbose_name = 'Уровень сложности'
        verbose_name_plural = 'Уровни сложности'

    def __str__(self):
        seasons = []
        if self.winter: seasons.append(f"зима: {self.winter}")
        if self.summer: seasons.append(f"лето: {self.summer}")
        if self.autumn: seasons.append(f"осень: {self.autumn}")
        if self.spring: seasons.append(f"весна: {self.spring}")
        return ", ".join(seasons) if seasons else "Не указано"


class Pereval(models.Model):
    """Основная модель перевала"""
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('pending', 'В работе'),
        ('accepted', 'Принят'),
        ('rejected', 'Отклонен'),
    ]

    beauty_title = models.CharField(max_length=255, verbose_name="Красивое название")
    title = models.CharField(max_length=255, verbose_name="Название")
    other_titles = models.CharField(max_length=255, verbose_name="Другие названия", blank=True)
    connect = models.CharField(max_length=255, verbose_name="Соединяет", blank=True)
    add_time = models.DateTimeField(auto_now_add=True, verbose_name="Время добавления")

    # Связи с другими моделями
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    coords = models.ForeignKey(Coords, on_delete=models.CASCADE, verbose_name="Координаты")
    level = models.ForeignKey(Level, on_delete=models.CASCADE, verbose_name="Уровень сложности")

    # Статус модерации
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="Статус"
    )

    class Meta:
        db_table = 'pereval'
        verbose_name = 'Перевал'
        verbose_name_plural = 'Перевалы'
        ordering = ['-add_time']

    def __str__(self):
        return f"{self.title} ({self.beauty_title}) - {self.get_status_display()}"


class Image(models.Model):
    """Модель изображения"""
    pereval = models.ForeignKey(Pereval, on_delete=models.CASCADE, related_name='images', verbose_name="Перевал")
    data = models.TextField(verbose_name="Данные изображения (base64)")  # Храним base64
    title = models.CharField(max_length=255, verbose_name="Название изображения")
    date_added = models.DateTimeField(auto_now_add=True, verbose_name="Время добавления")

    class Meta:
        db_table = 'pereval_image'
        verbose_name = 'Изображение'
        verbose_name_plural = 'Изображения'

    def __str__(self):
        return self.title