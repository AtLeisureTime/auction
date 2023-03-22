import collections.abc as abc
from typing import Any
import decimal
from django.http.request import HttpRequest
from django.http.response import HttpResponse
import django.contrib.postgres.search as postgresSearch
from django.views.generic import ListView, DetailView
import django.db.models as dj_models
from django.conf import settings as dj_settings
from . import models, utils, forms


class LotDetailView(DetailView):
    """ View for displaying lot object, stakes on it and other lot auction info.
    """
    model = models.Lot
    pk_url_kwarg = 'lotId'
    template_name = 'lot/stakes.html'
    context_object_name = 'lot'

    WS_PROTOCOL = 'ws'
    WSS_PROTOCOL = 'wss'

    def __getStakes(self) -> list[tuple]:
        """ Get all stakes for current lot.
        Returns:
            list[tuple]: [(timeOfStake, userMadeStake, stakeValue)]
        """
        stakes = []
        model = models.Stake
        lotPk = self.kwargs.get(self.pk_url_kwarg)
        stakesQueryset = model.objects.filter(lot_id=lotPk).all()
        for obj in reversed(stakesQueryset):
            stakes.append(
                (getattr(obj, model.TIME_N).strftime(utils.TIME_FORMAT),
                 getattr(obj, model.USER_N),
                 getattr(obj, model.STAKE_N))
            )
        return stakes

    def __calcNextMinStake(self, stakes: list[tuple]) -> decimal.Decimal:
        """ Calculate next minimal stake based on current leading stake.
        Args:
            stakes (list[tuple]): [(timeOfStake, userMadeStake, stakeValue)]
        Returns:
            Decimal: next minimal stake
        """
        nextMinStake = self.object.startPrice
        if stakes and stakes[0]:
            prevStake = stakes[0][-1]  # stakeValue of the leading stake
            nextMinStake = prevStake + utils.calcMinStakeStep(prevStake)
        return nextMinStake

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """ Collect additional data for displaying the lot.
        Returns:
            dict[str, Any]: context data
        """
        context = super().get_context_data(**kwargs)
        context['wsProtocol'] = self.WS_PROTOCOL if dj_settings.DEBUG else self.WSS_PROTOCOL
        context['stakeFields'] = models.Stake.UI_VN
        context['stakes'] = self.__getStakes()
        context['nextMinStake'] = self.__calcNextMinStake(context['stakes'])
        return context


class LotListView(ListView):
    """ View for displaying descriptions and auction info of lots,
        search form and lots filter by auction type.
    """
    template_name = 'lot/lot_list.html'
    context_object_name = 'lots'
    paginate_by = 3

    SEARCH_FIELD = 'description'
    MENU_SECTION = 'lots'

    def __getVisibleAuctnStates(self, isStaff: bool) -> abc.Iterable[tuple[str, str]]:
        """ Get all auction states of lots that are visible for user made request.
        Args:
            isStaff (bool): whether user from request can access the admin site.
        Returns:
            abc.Iterable[tuple[str, str]]: abc.Iterable[(auctnStateName, auctnStateVerboseName)]
        """
        auctnStates = models.Lot.AuctionStates.choices
        if not isStaff:
            auctnStates = filter(lambda state: state[0] != models.Lot.AuctionStates.DRAFT,
                                 auctnStates)
        return auctnStates

    def __getSearchForm(self, request: HttpRequest) -> forms.SearchForm:
        """ Create and return forms.SearchForm object.
        """
        if forms.SearchForm.QUERY_N in request.GET:
            searchForm = forms.SearchForm(request.GET)
        else:
            searchForm = forms.SearchForm()
        self.__searchForm = searchForm
        return searchForm

    def __getAllLeadingStakes(self) -> dict[dict]:
        """ Get leading stakes for all lots.
        Returns:
            dict: {lotId}:leadingStake
        """
        leadingStakesL = models.Stake.objects.order_by('lot_id', '-time').distinct('lot_id')\
            .values('lot_id', models.Stake.TIME_N, 'user__username', models.Stake.STAKE_N)
        leadingStakes = {}
        for stakeD in leadingStakesL:
            leadingStakes[stakeD.pop('lot_id')] = {
                'time': stakeD.get(models.Stake.TIME_N).strftime(utils.TIME_FORMAT),
                'username': stakeD.get('user__username'),
                'stake': stakeD.get(models.Stake.STAKE_N)
            }
        return leadingStakes

    def __getNumStakes(self) -> dict[int, int]:
        """ Get number of stakes for every lot at the current moment.
        Returns:
            dict: {lotId}:{numberOfStakes}
        """
        numStakesL = self.object_list.annotate(numStakes=dj_models.Count('stake'))\
            .values('id', 'numStakes')
        numStakes = {lotD.get('id'): lotD.pop('numStakes') for lotD in numStakesL}
        return numStakes

    def get_ordering(self) -> list[str]:
        if self.__auctnState in {models.Lot.AuctionStates.STARTED,
                                 models.Lot.AuctionStates.FINISHED}:
            return ['endTime']
        elif self.__auctnState == models.Lot.AuctionStates.NOT_STARTED:
            return ['startTime']
        elif self.__auctnState == models.Lot.AuctionStates.DRAFT:
            return ['lastModified']
        return []

    def get_queryset(self) -> dj_models.query.QuerySet:
        """ Get lots filtered by auction type and description for the view.
        Returns:
            dj_models.query.QuerySet: iterable of lots
        """
        if self.__auctnState in models.Lot.AuctionStates.values:
            queryset = models.Lot.objects.filter(auctionState=self.__auctnState)
        else:
            queryset = models.Lot.objects.all()
        if not self.__request.user.is_staff:
            queryset = queryset.exclude(auctionState=models.Lot.AuctionStates.DRAFT)

        # return queryset with the best match for search
        searchForm = self.__getSearchForm(self.__request)
        if searchForm.is_valid():
            query = searchForm.cleaned_data.get(forms.SearchForm.QUERY_N)
            if query:
                vector = postgresSearch.SearchVector(self.SEARCH_FIELD)
                query = postgresSearch.SearchQuery(query, search_type='plain')
                queryset = queryset.annotate(rank=postgresSearch.SearchRank(vector, query))\
                    .order_by('-rank')
                return queryset

        ordering = self.get_ordering()
        if ordering:
            queryset = queryset.order_by(*ordering)
        return queryset

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """ Collect additional data for displaying the list of lots.
        Returns:
            dict[str, Any]: context data
        """
        context = super().get_context_data(**kwargs)
        context['section'] = self.MENU_SECTION
        context['auctnState'] = self.__auctnState
        isStaff = self.__request.user.is_staff
        context['auctnStates'] = self.__getVisibleAuctnStates(isStaff)
        context['searchForm'] = self.__searchForm
        context['leadingStakes'] = self.__getAllLeadingStakes()
        context['numStakes'] = self.__getNumStakes()
        return context

    def get(self, request: HttpRequest, auctnState: str = None,
            *args: Any, **kwargs: Any) -> HttpResponse:
        """ Add object_list to the context, generate response.
        Args:
            request (HttpRequest): user request
            auctnState (str, optional): short name of auction state from models.Lot.AuctionStates.
                                        Defaults to None.
        Returns:
            HttpResponse: response for user
        """
        self.__request = request
        self.__auctnState = auctnState
        return super(LotListView, self).get(request, *args, **kwargs)
