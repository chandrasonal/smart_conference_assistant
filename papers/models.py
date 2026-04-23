from django.db import models


class Conference(models.Model):
    name = models.CharField(max_length=200)
    year = models.IntegerField()

    class Meta:
        ordering = ['-year', 'name']
        unique_together = [('name', 'year')]

    def __str__(self):
        return f"{self.name} {self.year}"


class Paper(models.Model):
    title      = models.CharField(max_length=500)
    authors    = models.TextField()
    abstract   = models.TextField()
    doi_url    = models.URLField(blank=True, default='')
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name='papers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
