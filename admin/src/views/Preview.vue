<template>
  <div class="preview-container">
    <div class="header">
      <div class="logo">⛵ FinanceSail</div>
    </div>
    
    <div class="content-wrapper">
      <div class="title-section">
        <h1 class="title">{{ content.title }}</h1>
        <div class="meta">
          <span class="market">{{ content.market }}</span>
          <span class="date">{{ content.created_at }}</span>
        </div>
      </div>

      <div class="images-section" v-if="content.image_urls && content.image_urls.length > 0">
        <h2>📊 Images</h2>
        <div class="images-grid">
          <div 
            v-for="(url, index) in content.image_urls" 
            :key="index" 
            class="image-item"
            @click="viewImage(index)"
          >
            <img :src="url" :alt="`Image ${index + 1}`" />
            <div class="image-overlay">
              <el-button 
                type="primary" 
                size="small" 
                circle 
                @click.stop="downloadImage(url, index)"
              >
                <el-icon><Download /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <div class="content-section">
        <h2>📝 Content</h2>
        <div class="content-box">
          <pre>{{ content.content }}</pre>
        </div>
      </div>

      <div class="tags-section" v-if="content.tags">
        <h2>🏷️ Tags</h2>
        <div class="tags">
          <span v-for="tag in parseTags(content.tags)" :key="tag" class="tag">
            {{ tag }}
          </span>
        </div>
      </div>

      <div class="actions">
        <el-button type="primary" @click="copyTitle">
          <el-icon><Document /></el-icon>
          Copy Title
        </el-button>
        <el-button type="success" @click="copyContent">
          <el-icon><Document /></el-icon>
          Copy Content
        </el-button>
        <el-button type="warning" @click="copyTags">
          <el-icon><PriceTag /></el-icon>
          Copy Tags
        </el-button>
        <el-button type="info" @click="copyAll">
          <el-icon><CopyDocument /></el-icon>
          Copy All
        </el-button>
      </div>
    </div>

    <el-image-viewer
      v-if="showViewer"
      :url-list="content.image_urls"
      :initial-index="viewerIndex"
      @close="showViewer = false"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, PriceTag, CopyDocument, Download } from '@element-plus/icons-vue'
import axios from 'axios'

const route = useRoute()
const content = ref({
  id: 0,
  market: '',
  content_type: '',
  title: '',
  content: '',
  tags: '',
  image_urls: [],
  created_at: ''
})
const showViewer = ref(false)
const viewerIndex = ref(0)

const parseTags = (tags) => {
  if (!tags) return []
  return tags.split(' ').filter(tag => tag.trim())
}

const viewImage = (index) => {
  viewerIndex.value = index
  showViewer.value = true
}

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('Copied to clipboard!')
  } catch (err) {
    ElMessage.error('Failed to copy')
  }
}

const copyTitle = () => {
  copyToClipboard(content.value.title)
}

const copyContent = () => {
  copyToClipboard(content.value.content)
}

const copyTags = () => {
  copyToClipboard(content.value.tags)
}

const copyAll = () => {
  const all = `${content.value.title}\n\n${content.value.content}\n\n${content.value.tags}`
  copyToClipboard(all)
}

const downloadImage = (url, index) => {
  const link = document.createElement('a')
  link.href = url
  link.download = `image_${index + 1}.png`
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  ElMessage.success('Download started!')
}

const fetchContent = async () => {
  try {
    const response = await axios.get(`/api/preview/${route.params.id}`)
    content.value = response.data
  } catch (error) {
    console.error('Failed to fetch content:', error)
    ElMessage.error('Failed to load content')
  }
}

onMounted(() => {
  fetchContent()
})
</script>

<style scoped>
.preview-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.header {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.logo {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.content-wrapper {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 24px;
}

.title-section {
  margin-bottom: 24px;
  text-align: center;
}

.title {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px 0;
  line-height: 1.4;
}

.meta {
  display: flex;
  justify-content: center;
  gap: 12px;
  color: #909399;
  font-size: 14px;
}

.market {
  background: #409eff;
  color: #fff;
  padding: 4px 12px;
  border-radius: 4px;
  font-weight: 500;
}

.images-section,
.content-section,
.tags-section {
  margin-bottom: 24px;
}

h2 {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 16px 0;
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}

.image-item {
  aspect-ratio: 1;
  overflow: hidden;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s;
  position: relative;
}

.image-item:hover {
  transform: scale(1.02);
}

.image-overlay {
  position: absolute;
  bottom: 8px;
  right: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.image-item:hover .image-overlay {
  opacity: 1;
}

.image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.content-box {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
}

.content-box pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'SF Mono', Monaco, 'Inconsolata', 'Roboto Mono', 'Source Code Pro', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  background: #ecf5ff;
  color: #409eff;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 14px;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #eee;
}

/* 手机端适配 */
@media (max-width: 768px) {
  .preview-container {
    padding: 12px;
  }

  .content-wrapper {
    padding: 16px;
    border-radius: 8px;
  }

  .title {
    font-size: 22px;
  }

  .meta {
    flex-direction: column;
    gap: 8px;
  }

  .images-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }

  .actions {
    flex-direction: column;
  }

  .actions .el-button {
    width: 100%;
  }
}
</style>