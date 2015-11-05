__author__ = 'Taylor'
import json
from django.db.models import Q
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view
from leaa.models import Terrain, Station, DataFile, Setting
from django.contrib.auth.models import User
from fileReader import readSDR, readTerrain  # readRecordDateToString, dateStringToDate

@api_view(['GET'])
def getDates(request):
    terrainID = request.GET.get('terrainID')
    stations = Station.objects.filter(terrain=terrainID)
    dates = []
    stationNames = []
    for station in stations:
        stationNames.append(station.name)
        datafile = DataFile.objects.filter(station=station)
        for file in datafile:
            date = str(file.creationDate)[:10]
            if not (date in dates):
                dates.append(date)
    result = {'dates':dates, 'stationNames':stationNames}
    return HttpResponse(json.dumps(result), status=status.HTTP_200_OK)


@api_view(['GET'])
def getStationObjects(request):
    stationNames = request.GET.getlist('stations[]')
    recordDate = str(request.GET.get('recordDate'))
    result = {}
    for stationName in stationNames:
        stationResult = {}
        station = Station.objects.get(name=stationName)
        query = Q(creationDate=recordDate) & Q(station=station)

        # Try to get file from disk. If we have an error, we just bail
        # TODO: Make this better
        try:
            file = DataFile.objects.get(query)
            # Get data from file on disk
            heights, dates, speeds, directions = readSDR(file, station)
            stationResult = {'heights': heights, 'dates': dates, 'speeds': speeds, 'directions': directions}
            # Get data from sqlite db
            stationResult['name']       = station.name
            stationResult['demX']       = station.demX
            stationResult['demY']       = station.demY
            stationResult['lat']        = station.lat
            stationResult['long']       = station.long
            stationResult['terrain']    = station.terrain_id
            stationResult['id'] = station.id
        except:
            continue
        result[stationName] = stationResult
        '''
        datafiles = DataFile.objects.filter(query)
        if len(datafiles) != 0:
            for file in datafiles:
                # Get data from file on disk
                heights, dates, speeds, directions = readSDR(file, station)
                stationResult = {'heights': heights, 'dates': dates, 'speeds': speeds, 'directions': directions}
                # Get data from sqlite db
                stationResult['name']       = station.name
                stationResult['demX']       = station.demX
                stationResult['demY']       = station.demY
                stationResult['lat']        = station.lat
                stationResult['long']       = station.long
                stationResult['terrain']    = station.terrain_id
                stationResult['id'] = station.id
            result[stationName] = stationResult
        '''
    return HttpResponse(json.dumps(result), status=status.HTTP_200_OK)


@api_view(['GET'])
def getTerrain(request):
    terrain = Terrain.objects.get(pk=request.GET.get('terrainID'))
    file = readTerrain(terrain)
    return HttpResponse(file, status=status.HTTP_200_OK)


@api_view(['GET'])
def getSettings(request):
    result = {}
    if request.user.is_authenticated():
        user = User.objects.get(username=request.user.username)
        settings = Setting.objects.get(user=user)
        result['VectorHeight'] = settings.vectorHeight
        result['VectorLength'] = settings.vectorLength
        result['SceneHeight'] = settings.sceneHeight
        result['ArrowColor'] = settings.vectorColor
        result['LiveUpdate'] = settings.liveUpdate
        return HttpResponse(json.dumps(result), status=status.HTTP_200_OK)
    else:
        return HttpResponse(json.dumps(result), status=status.HTTP_200_OK)


@csrf_exempt
def setSettings(request):
    if request.user.is_authenticated():
        settings = Setting.objects.get(user=User.objects.get(username=request.user.username))
        settings.liveUpdate = bool(request.POST['live'])
        settings.vectorColor = request.POST['color']
        settings.sceneHeight = float(request.POST['sheight'])
        settings.vectorLength = float(request.POST['vlength'])
        settings.vectorHeight = float(request.POST['vheight'])
        settings.save()
        return HttpResponse(status=status.HTTP_200_OK)
    else:
        return HttpResponse(status=status.HTTP_511_NETWORK_AUTHENTICATION_REQUIRED)
