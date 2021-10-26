from django.urls import reverse_lazy
from django.views.generic import FormView
from django.conf import settings
import requests, json
from django.http import HttpResponse
from .models import Settings
from .form import ControllerForm


# Create your views here.
class ControllerView(FormView):
    form_class = ControllerForm
    template_name = 'core/control.html'
    success_url = reverse_lazy('form')
    headers = {'Authorization': settings.SMART_HOME_ACCESS_TOKEN}
    api_url = settings.SMART_HOME_API_URL
    data = dict()

    def get(self, request, *args, **kwargs):
        request = requests.get(self.api_url, headers=self.headers)
        if request.status_code == 200:
            detectors = request.json()['data']
            self.data = {dic['name']: dic['value'] for dic in detectors}
            return super(ControllerView, self).get(request)
        else:
            return HttpResponse(status='502')

    def post(self, request, *args, **kwargs):
        request = requests.get(self.api_url, headers=self.headers)
        if request.status_code == 200:
            detectors = request.json()['data']
            self.data = {dic['name']: dic['value'] for dic in detectors}
            return super(ControllerView, self).post(request)
        else:
            return HttpResponse(status='502')

    def get_context_data(self, **kwargs):
        context = super(ControllerView, self).get_context_data()
        context['data'] = self.data
        return context

    def get_initial(self):
        return {
            'bedroom_target_temperature': Settings.objects.get(controller_name='bedroom_target_temperature').value,
            'hot_water_target_temperature': Settings.objects.get(controller_name='hot_water_target_temperature').value,
            'bedroom_light': self.data['bedroom_light'],
            'bathroom_light': self.data['bathroom_light'],
        }

    def form_valid(self, form):
        sensors = list()

        if form.cleaned_data['bedroom_light'] != self.data['bedroom_light']:
            sensors.append({"name": "bedroom_light", "value": form.cleaned_data['bedroom_light']})

        if form.cleaned_data['bathroom_light'] != self.data['bathroom_light']:
            sensors.append({"name": "bathroom_light", "value": form.cleaned_data['bathroom_light']})

        if len(sensors) != 0 and not self.data['smoke_detector']:
            payload = {"controllers": sensors}
            post = requests.post(self.api_url, data=json.dumps(payload), headers=self.headers)
            if post.status_code != 200:
                return HttpResponse(status='502')

        bedroom_temp = Settings.objects.get(controller_name='bedroom_target_temperature')
        bedroom_temp.value = form.cleaned_data['bedroom_target_temperature']
        bedroom_temp.save()

        hot_water_temp = Settings.objects.get(controller_name='hot_water_target_temperature')
        hot_water_temp.value = form.cleaned_data['hot_water_target_temperature']
        hot_water_temp.save()

        return super(ControllerView, self).form_valid(form)