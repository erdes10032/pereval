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


class Coords(models.Model):
    """Модель координат"""
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    height = models.IntegerField()

    class Meta:
        db_table = 'pereval_coords'


class Level(models.Model):
    """Модель уровня сложности"""
    winter = models.CharField(max_length=10, blank=True)
    summer = models.CharField(max_length=10, blank=True)
    autumn = models.CharField(max_length=10, blank=True)
    spring = models.CharField(max_length=10, blank=True)

    class Meta:
        db_table = 'pereval_level'


class Pereval(models.Model):
    """Основная модель перевала"""
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('pending', 'В работе'),
        ('accepted', 'Принят'),
        ('rejected', 'Отклонен'),
    ]

    beauty_title = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    other_titles = models.CharField(max_length=255, blank=True)
    connect = models.CharField(max_length=255, blank=True)
    add_time = models.DateTimeField(auto_now_add=True)

    # Связи с другими моделями
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coords = models.ForeignKey(Coords, on_delete=models.CASCADE)
    level = models.ForeignKey(Level, on_delete=models.CASCADE)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'  # Автоматически 'new' при создании
    )

    class Meta:
        db_table = 'pereval'