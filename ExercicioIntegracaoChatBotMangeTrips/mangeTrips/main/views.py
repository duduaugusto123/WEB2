from .models import *
from .serializers import *
from rest_framework import status
from rest_framework.response import Response

from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from datetime import timedelta, datetime

from django_filters.rest_framework import DjangoFilterBackend
from .customFilters import *
from rest_framework import filters
from django.db.models import Avg, Q

from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser, IsAuthenticated, DjangoModelPermissionsOrAnonReadOnly

from ai import train, chat
from django.http import JsonResponse

from django.core.exceptions import ObjectDoesNotExist

def strToDate(strDate):
    return datetime.strptime(strDate, '%Y-%m-%d').date()

class CustomModelViewSet(ModelViewSet):
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=isinstance(request.data, list))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class ScoreAverageView(APIView):

    def get(self, request, tripId = ''):
        if tripId == '': return Response(status=400,data='Missing required parameter tripId')
        try:
            tripFound = Trip.objects.get(id=tripId)
            serializerTrip = TripSerializer(tripFound, many=False)
            average = Booking.objects.filter(tripFK=tripId).aggregate(Avg('score'))
            if average is not None: return Response(status=200, data={'average': average['score__avg'], 'trip': serializerTrip.data}) 
            else: return Response(status=404,data='Getting Average of this trip is not possible')

        except Trip.DoesNotExist:
            return Response(status=404, data='Trip was not found!')


class CategoryView(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class  = CategoryFilter
    ordering_fields = '__all__'
    # permission_classes = (DjangoModelPermissionsOrAnonReadOnly,)   


class TripView(ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class  = TripFilter
    ordering_fields = '__all__'
    # permission_classes = (IsAuthenticatedOrReadOnly,)   

class ImageView(CustomModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    # permission_classes = (DjangoModelPermissionsOrAnonReadOnly,)   

class CustomUserView(ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class  = CustomUserFilter
    ordering_fields = '__all__'    

class BookingView(ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class  = BookingFilter
    ordering_fields = '__all__'
    # permission_classes = (IsAuthenticated,)   


    def create(self, request, *args, **kwargs): 
        data = request.data
        #transform a period in a list of dates
        dayList = []
        availabilities = []
        currentDate = strToDate(data['startDate'])
        while currentDate <= strToDate(data['endDate']):
            dayList.append(currentDate)
            currentDate += timedelta(days=1)

        #check date availability
        for dateChosen in dayList:            
            
            availability = Availability.objects.filter(tripFK=data['tripFK']).filter(date=dateChosen).filter(bookingFK=None).first()
            if availability is None: 
                return Response(status=409,data='Period between ' + data['startDate'] + ' and ' + data['endDate'] + ' is not available! Please, consider another one')

            availabilities.append(availability)
            
        savedBookingResponse = super(BookingView, self).create(request,*args,**kwargs)
        if savedBookingResponse.status_code == 201:   
            savedBooking = Booking.objects.get(pk=savedBookingResponse.data['id'])
            for availability in availabilities:
                availability.bookingFK = savedBooking
                availability.save()
            return Response(status=201,data=savedBookingResponse.data)
        else:
            return Response(status=500,data='Error when saving booking!')


class PaymentView(ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer   
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class  = PaymentFilter
    ordering_fields = '__all__'
    # permission_classes = (IsAuthenticated,)   
    
    def get_queryset(self):
        user = self.request.user
        queryset = None
        if user.is_superuser:
            queryset = Payment.objects.all()
        else:
            queryset = Payment.objects.filter(bookingFK__customUserFK__user__username=user.username)
        return queryset 



class AvailabilityView(CustomModelViewSet):
    queryset = Availability.objects.all()
    serializer_class = AvailabilitySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class  = AvailabilityFilter
    ordering_fields = '__all__' 
    # permission_classes = (DjangoModelPermissionsOrAnonReadOnly,)  


def convertToMessage(data,attributeName):
    index = 1
    response = ' \n '
    for dt in data:
        response += str(index) + '- ' + getattr(dt,attributeName,None) + ' \n '
        index += 1
    return response

class ChatBotAPIView(APIView):
   
    def post(self, request):
        data = request.data
        question = data.get('question')
        conversationId = data.get('conversationId')
        userId = data.get('userId')
        
        userFound = None
        #checa se o usuário existe
        try:
            userFound = User.objects.get(pk=userId)
        except ObjectDoesNotExist:
            return JsonResponse(status=500,data={'content': 'Usuário não encontrado!'})

        conversationFound = None

        #nova conversa!
        if conversationId is None:
            newHistory = ConversationHistory(user=userFound)
            newHistory.save()
            conversationFound = newHistory
        #contexto de uma conversa já existente (front enviou o conversationId)
        #checa se a conversa existe
        else:
            try:
                conversationFound = ConversationHistory.objects.get(pk=conversationId)
            except ObjectDoesNotExist:
                return JsonResponse(status=500,data={'content': 'Conversa não encontrada!'})

        #salva a pergunta no banco, linkando com o histórico
        newQuestion = Conversation(type="Q",message=question,history=conversationFound)
        newQuestion.save()
        
        #chama a I.A.
        answer = chat.get_response(question)
        finalMessage = answer.message

        newAnswer = None
        if conversationFound.lastCommand == 'SEARCH_TRIP':
            if answer.command == 'EXIT_SEARCH_TRIP':
                print('SAIA')
                conversationFound.lastCommand=''
                conversationFound.save()
            else:
                trips = Trip.objects.filter(Q(title__icontains=question) | Q(description__icontains=question) | Q(city__icontains=question))
                if trips.exists():
                    finalMessage = convertToMessage(trips,'title')
                else:                
                    finalMessage = 'Infelizmente não encontramos a viagem que procura =/'
                
                newAnswer = Conversation(type="A",message=finalMessage,history=conversationFound)

            

        elif answer.command == 'LIST_TRIPS':
            trips = Trip.objects.all()
            finalMessage += convertToMessage(trips,'title')
            newAnswer = Conversation(type="A",message=finalMessage if answer.additionalMessage is None else finalMessage + '\n' + answer.additionalMessage ,history=conversationFound)
        else:
            #atualiza o último comando interpretado pela I.A.
            conversationFound.lastCommand = answer.command
            conversationFound.save()
            newAnswer = Conversation(type="A",message=finalMessage if answer.additionalMessage is None else finalMessage + '\n' + answer.additionalMessage ,history=conversationFound)
        
        newAnswer.save()
        
        serializedAnswer = ConversationSerializer(newAnswer,many=False)
               
        return JsonResponse(status=201, data=serializedAnswer.data)

class ConversationHistoryView(ModelViewSet):

    queryset = ConversationHistory.objects.all()
    serializer_class = ConversationHistorySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = '__all__' 

    def get_queryset(self):
        
            historyId = self.request.query_params['historyId']

            

            if(historyId == ''):
                return JsonResponse(status=400,data={'content': 'Missing required parameter historyId'})
            else:
                try:
                    return ConversationHistory.objects.filter(user__pk=historyId)
                    

                except ObjectDoesNotExist:
                    return JsonResponse(status=500,data={'content': 'Histórico não encontrado!'})
                
class ConversationView(ModelViewSet):

    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = '__all__' 
