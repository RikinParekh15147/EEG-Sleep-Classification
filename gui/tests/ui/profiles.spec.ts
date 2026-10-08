import {test,expect} from '@playwright/test';
import fs from 'node:fs';

test('all four reference profiles expose domains and complete biomarker comparisons',async({page})=>{
 await page.goto('/');
 await page.getByRole('button',{name:'Results explorer',exact:true}).click();
 await page.getByRole('button',{name:'Sleep profile',exact:true}).click();
 for(const [id,level,count] of [['SN001','High Deviation',3],['SN004','High Deviation',3],['SN009','Mild Deviation',1],['SN022','Moderate Deviation',2]] as const){
  await page.getByRole('combobox',{name:'Results recording'}).selectOption(id);
  await expect(page.getByText(level,{exact:true})).toBeVisible();
  await expect(page.getByText(`${count} of 4 domains deviate`,{exact:true})).toBeVisible();
  await expect(page.locator('tbody tr')).toHaveCount(21);
  await expect(page.getByRole('columnheader',{name:'z-score',exact:true})).toBeVisible();
  if(id==='SN001')await expect(page.getByText(/SN001 covers 190 epochs/)).toBeVisible();
 }
 await page.getByRole('combobox',{name:'Results recording'}).selectOption('SN009');
 fs.mkdirSync('../refinement_artifacts/verified',{recursive:true});
 await page.screenshot({path:'../refinement_artifacts/verified/dashboard-full.png',fullPage:true});
 await page.screenshot({path:'../refinement_artifacts/verified/dashboard.png'});
 await page.getByRole('button',{name:'Toggle color theme'}).click();
 await page.setViewportSize({width:390,height:844});
 await expect(page.getByRole('heading',{name:'Sleep-health deviation profile'})).toBeVisible();
 await page.screenshot({path:'.runtime/screenshots/profile-mobile.png',fullPage:true});
});
