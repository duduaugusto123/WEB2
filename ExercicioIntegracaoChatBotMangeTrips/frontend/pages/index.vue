<script setup>
    let response = ref("")
    const dialog = reactive({
        text: '',
        type: '',
        name: '',
        image: '',
        historyId: null
    });

    const includeDialog = ((type)=>{
        if(type === 'Q'){
            dialog.image = 'user.png';
            dialog.name = 'André';            
            dialog.type = 'right';
        } else {
            dialog.image = 'bot.png';
            dialog.name = 'Bot';            
            dialog.type = 'left';
        }
        // faz a cópia profunda da estrutura com os valores atuais (deep copy)
        conversationHistory.value.push(
            JSON.parse(JSON.stringify(dialog))
        );                
    });
    
    const sendMessage = async () => {
        console.log(dialog.text);
        includeDialog('Q');
        
        //message.value;
        const {data: answer} = await useFetch('http://localhost:8000/chatbot/',{
            method: 'POST',
            body:{
                question: dialog.text,
                userId: 1,
                conversationId: dialog.historyId
            }   
        })
        dialog.text = answer.value.message
        dialog.historyId = answer.value.history.id
        includeDialog('A');
        dialog.text = ''
    }

//armazena em tela o histórico das mensagens
const conversationHistory = ref([])
const {data:ConversationHistory} = await useFetch('http://localhost:8000/conversation/?historyId=1')

</script>

<template>
    <div>
        <div v-for="(conversation, id) in conversationHistory" :key="id">
            <TextBox :name="conversation.name" :avatarImage="conversation.image" 
                :message="conversation.text" :type="conversation.type"/>
        </div>
        <label for=""> Type here your message!</label> <br>
        <textarea v-model="dialog.text"/> <br> <br>        
        <Button @click="sendMessage" label="Send"></Button>
        <hr>
        <div>
            <h5>Bard: 😎</h5>
            <p> {{ response }} </p>
        </div>
        <div class="conteinerSideBar" v-for="(ConversaHistoria,index) in ConversationHistory.results" :key="index">
            <h5>{{ConversaHistoria.lastCommand}}</h5>
        </div>
    </div>
</template>

<style scoped>
     
    /* button{
        background-color: black;
        color: white;
    } */
</style>