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


class PerevalAreas(models.Model):
    """Модель регионов/областей"""
    id = models.BigIntegerField(primary_key=True)
    id_parent = models.BigIntegerField(verbose_name="ID родительского региона")
    title = models.TextField(verbose_name="Название региона")

    class Meta:
        db_table = 'pereval_areas'
        verbose_name = 'Регион'
        verbose_name_plural = 'Регионы'

    def __str__(self):
        return f"{self.title} (ID: {self.id}, Родитель: {self.id_parent})"


class SprActivitiesTypes(models.Model):
    """Модель видов активностей"""
    id = models.IntegerField(primary_key=True)
    title = models.TextField(verbose_name="Вид активности")

    class Meta:
        db_table = 'spr_activities_types'
        verbose_name = 'Вид активности'
        verbose_name_plural = 'Виды активностей'

    def __str__(self):
        return self.title


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
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь", related_name='perevals')
    coords = models.ForeignKey(Coords, on_delete=models.CASCADE, verbose_name="Координаты", related_name='perevals')
    level = models.ForeignKey(Level, on_delete=models.CASCADE, verbose_name="Уровень сложности",
                              related_name='perevals')

    area = models.ForeignKey(
        PerevalAreas,
        on_delete=models.SET_NULL,
        verbose_name="Регион",
        null=True,
        blank=True,
        related_name='perevals'
    )

    activity_type = models.ForeignKey(
        SprActivitiesTypes,
        on_delete=models.SET_NULL,
        verbose_name="Вид активности",
        null=True,
        blank=True,
        related_name='perevals'
    )

    # Статус
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

    def can_be_edited(self):
        """Проверка, можно ли редактировать запись"""
        return self.status == 'new'


class Image(models.Model):
    """Модель изображения"""
    pereval = models.ForeignKey(Pereval, on_delete=models.CASCADE, related_name='images', verbose_name="Перевал")
    image = models.ImageField(upload_to='pereval_images/%Y/%m/%d/', verbose_name="Изображение")
    title = models.CharField(max_length=255, verbose_name="Название изображения")
    date_added = models.DateTimeField(auto_now_add=True, verbose_name="Время добавления")

    class Meta:
        db_table = 'pereval_image'
        verbose_name = 'Изображение'
        verbose_name_plural = 'Изображения'

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        """Удаление файла изображения при удалении записи"""
        if self.image:
            storage, path = self.image.storage, self.image.path
            super().delete(*args, **kwargs)
            storage.delete(path)
        else:
            super().delete(*args, **kwargs)
