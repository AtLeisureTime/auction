from django.contrib import admin
from lot import models


class StakeInline(admin.TabularInline):
    model = models.Stake


@admin.register(models.Lot)
class LotAdmin(admin.ModelAdmin):
    list_display = ['id', 'description', 'startTime', 'endTime', 'auctionState', 'startPrice']
    list_filter = ['auctionState', 'startTime', 'endTime']
    inlines = [StakeInline]


@admin.register(models.Stake)
class StakeAdmin(admin.ModelAdmin):
    list_display = ['id', models.Stake.LOT_N, models.Stake.USER_N, models.Stake.TIME_N,
                    models.Stake.STAKE_N]
    raw_id_fields = [models.Stake.LOT_N, models.Stake.USER_N]
