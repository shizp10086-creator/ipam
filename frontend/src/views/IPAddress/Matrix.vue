<template>
  <div class="ip-matrix">
    <h3>IP 矩阵视图 - 网段 #{{ segmentId }}</h3>
    <p style="color: #909399;">以网格形式展示网段内所有 IP 地址状态</p>
    <el-empty description="IP 矩阵视图 - 待完善" />
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
const route = useRoute()
const segmentId = route.params.segmentId
</script>
