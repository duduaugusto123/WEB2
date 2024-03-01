<script setup>

    


    const id = ref(0)
    const { data: conversationHistory } = await useFetch('http://localhost:8000/conversationhistory/?historyId=1')
    const { data: conversation } = await useFetch(`http://localhost:8000/conversation/`)    
    console.log(conversationHistory)
    console.log(conversation)
    var idsHistory = []
    for(let x in conversationHistory.value.results){
        idsHistory.push(parseInt(conversationHistory.value.results[x].id)) 
        console.log(idsHistory)
    }
    console.log(conversation.value.results[0].type == 'Q')

    
    const evento = defineEmits(['SendHistoryId']);
    
    const sendIdHistoric = ((id) => {
        console.log(id);        
        evento('SendHistoryId',id)
    });
</script>

<template>
    <!-- // (idsHistory[index] == conversation.results[index].history.id) -->
    <div>
        <div class="conteinerSideBar" v-for="(conv, index) in (conversation.results.length-1)" :key="index">

            <button id="button_history" v-if="conversation.results[index].type == 'Q' && conversation.results[index].history.id in idsHistory" @click="sendIdHistoric(conversation.results[index].history.id)">
                {{conversation.results[index].message}}
            </button>
        </div>
    </div>
</template>

<style>
    #button_history{
        display: flex;
        justify-content: center;
        align-items: center;
        border-top: 1px solid #161616;
        border-bottom: 1px solid #161616;
        background-color: transparent;
        text-align: center;
    }
</style>