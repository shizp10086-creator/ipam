<template>
  <div class="ai-page">
    <h3 style="margin-bottom:16px;">🤖 AI 运维助手</h3>
    <el-row :gutter="16">
      <el-col :span="16">
        <el-card class="chat-card">
          <div class="chat-messages" ref="msgBox">
            <div v-for="(msg,i) in messages" :key="i" :class="['msg', msg.role]">
              <div class="msg-avatar">{{ msg.role==='user'?'👤':'🤖' }}</div>
              <div class="msg-content">
                <div class="msg-text" style="white-space:pre-wrap;">{{ msg.text }}</div>
                <div class="msg-time">{{ msg.time }}</div>
              </div>
            </div>
            <div v-if="messages.length===0" style="text-align:center;color:#909399;padding:40px;">
              <p style="font-size:32px;">🤖</p>
              <p>你好！我是 AI 运维助手，可以帮你：</p>
              <p style="font-size:13px;">查询资源状态 · 分析告警 · 排查故障 · 获取配置建议</p>
            </div>
          </div>
          <div class="chat-input">
            <el-input v-model="input" placeholder="输入问题，如：如何分配 IP？最近有什么告警？" @keyup.enter="send" :disabled="sending">
              <template #append><el-button type="primary" @click="send" :loading="sending">发送</el-button></template>
            </el-input>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>快捷问题</template>
          <div v-for="q in quickQuestions" :key="q" class="quick-q" @click="askQuick(q)">{{ q }}</div>
        </el-card>
        <el-card style="margin-top:12px;">
          <template #header>AI 模型</template>
          <el-table :data="models" size="small">
            <el-table-column prop="name" label="模型" width="120" />
            <el-table-column prop="provider" label="提供商" width="80" />
            <el-table-column label="状态" width="70"><template #default="{row}"><el-tag :type="row.status==='available'?'success':'info'" size="small">{{ row.status==='available'?'可用':'未配置' }}</el-tag></template></el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
<script setup>
import { ref, nextTick, onMounted } from 'vue'
import request from '@/api/request'
const input=ref(''),sending=ref(false),messages=ref([]),models=ref([]),msgBox=ref(null)
const quickQuestions=['如何分配 IP 地址？','最近有什么告警？','网段使用率怎么查看？','如何排查网络故障？','怎么创建工单？']
async function send(){
  if(!input.value.trim()||sending.value)return
  const q=input.value.trim();input.value=''
  messages.value.push({role:'user',text:q,time:new Date().toLocaleTimeString()})
  await nextTick();if(msgBox.value)msgBox.value.scrollTop=msgBox.value.scrollHeight
  sending.value=true
  try{
    const r=await request.post('/ai/chat',{message:q})
    messages.value.push({role:'ai',text:r.data?.reply||'抱歉，暂时无法回答',time:new Date().toLocaleTimeString()})
  }catch(e){messages.value.push({role:'ai',text:'网络错误，请稍后重试',time:new Date().toLocaleTimeString()})}
  sending.value=false
  await nextTick();if(msgBox.value)msgBox.value.scrollTop=msgBox.value.scrollHeight
}
function askQuick(q){input.value=q;send()}
async function loadModels(){try{const r=await request.get('/ai/models');models.value=r.data?.items||[]}catch(e){}}
onMounted(loadModels)
</script>
<style scoped>
.chat-card{height:calc(100vh - 180px);display:flex;flex-direction:column;}
.chat-card :deep(.el-card__body){flex:1;display:flex;flex-direction:column;padding:0;}
.chat-messages{flex:1;overflow-y:auto;padding:16px;}
.chat-input{padding:12px;border-top:1px solid #ebeef5;}
.msg{display:flex;gap:8px;margin-bottom:16px;}
.msg.user{flex-direction:row-reverse;}
.msg-avatar{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;}
.msg-content{max-width:70%;}
.msg.user .msg-content{text-align:right;}
.msg-text{padding:10px 14px;border-radius:12px;font-size:14px;line-height:1.6;}
.msg.user .msg-text{background:#409eff;color:#fff;border-bottom-right-radius:4px;}
.msg.ai .msg-text{background:#f5f7fa;color:#303133;border-bottom-left-radius:4px;}
.msg-time{font-size:11px;color:#c0c4cc;margin-top:4px;}
.quick-q{padding:8px 12px;margin-bottom:6px;background:#f5f7fa;border-radius:6px;cursor:pointer;font-size:13px;transition:background 0.2s;}
.quick-q:hover{background:#ecf5ff;color:#409eff;}
</style>
