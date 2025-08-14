from django.shortcuts import render
from django.views.generic import TemplateView


class HomeView(TemplateView):
    """
    Home page view that shows the BidLord landing page
    """
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'BidLord - Bidding Platform API',
            'description': 'A comprehensive bidding platform API built with Django REST Framework',
        })
        return context
